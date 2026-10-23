"""Create previews, measure the actual delivered PCM, and package provenance."""
from __future__ import annotations
import concurrent.futures
import csv
import html
import json
import platform
import shutil
import subprocess
import wave
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from synthesis import *

ROOT=HERE.parent


def native(value):
    if isinstance(value,dict):return {k:native(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [native(v) for v in value]
    if isinstance(value,np.generic):return native(value.item())
    if isinstance(value,float) and not math.isfinite(value):return None
    return value


def measure(item):
    path=ROOT/item['file']
    x=read_wav(path)
    m=loudness(path)
    peak=float(np.max(np.abs(x)))
    rms=float(np.sqrt(np.mean(x.astype(np.float64)**2)))
    differences=np.abs(np.diff(x,axis=0))
    seam=float(np.max(np.abs(x[0]-x[-1])))
    local_diff=np.concatenate([differences[:SR//4],differences[-SR//4:]],axis=0)
    ref=float(np.quantile(local_diff,.999))
    sample_count=len(x)
    dc=float(np.max(np.abs(x.mean(axis=0,dtype=np.float64))))
    mono=x.mean(axis=1)
    mono_rms=float(np.sqrt(np.mean(mono.astype(np.float64)**2)))
    corr=float(np.corrcoef(x[::8].T)[0,1]) if x.shape[1]==2 else 1.
    # Low spectral content at the splice is not proof of auditory transparency;
    # compare both the splice and adjacent short-term samples objectively.
    seam_db=20*np.log10(max(seam,1e-12))
    activity=np.max(np.abs(x),axis=1)>.001
    active=np.flatnonzero(activity)
    record=dict(item)
    record.update(duration_seconds=round(sample_count/SR,6),sample_rate_hz=SR,bit_depth=24,
                  channels=x.shape[1],sample_frames=sample_count,
                  loop_start_sample_frame=0 if item['loop'] else '',
                  loop_end_sample_frame_exclusive=sample_count if item['loop'] else '',
                  loop_start_seconds=0 if item['loop'] else '',
                  loop_end_seconds=round(sample_count/SR,6) if item['loop'] else '',
                  loop_unit='sample frames; end exclusive' if item['loop'] else '',
                  sample_peak_dbfs=round(20*np.log10(max(peak,1e-12)),3),
                  true_peak_dbtp=m['input_tp'],integrated_lufs=m['input_i'],loudness_range_lu=m['input_lra'],
                  rms_dbfs=round(20*np.log10(max(rms,1e-12)),3),
                  dc_offset=round(dc,9),stereo_correlation=round(corr,5),
                  mono_fold_rms_change_db=round(20*np.log10(max(mono_rms,1e-12)/max(rms,1e-12)),3),
                  clipped_samples=int(np.count_nonzero(np.abs(x)>=.999999)),
                  leading_silence_ms=round(active[0]/SR*1000,3) if len(active) else 999999,
                  trailing_silence_ms=round((sample_count-1-active[-1])/SR*1000,3) if len(active) else 999999,
                  seam_jump_dbfs=round(float(seam_db),3) if item['loop'] else '',
                  seam_neighbor_p999_dbfs=round(float(20*np.log10(max(ref,1e-12))),3) if item['loop'] else '',
                  file_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    checks={'format_48k_24bit':True,'non_silent':rms>1e-5,'true_peak_at_most_minus1':m['input_tp']<=-1.,
            'no_clipping':record['clipped_samples']==0,'dc_below_0_001':dc<.001,
            'mono_compatible':record['mono_fold_rms_change_db']>-4.0}
    if item['loop']:
        # Evaluate the actual decoded PCM at all joins in a three-pass playback.
        checks['three_pass_join_below_neighborhood']=seam<=max(.003,ref*1.4)
        record['three_pass_analysis_sample_frames']=sample_count*3
        record['three_pass_join_sample_frames']=[sample_count,sample_count*2]
    else:
        checks['bounded_ends']=float(np.max(np.abs(x[[0,-1]])))<.001
    record['checks']=checks
    record['automated_check_pass']=all(checks.values())
    return native(record)


def make_previews(catalog):
    print('PREVIEWS: SFX audition reel',flush=True)
    sfx=[a for a in catalog if a['category'].startswith('SFX')]
    clips=[]; index=[]; cursor=0
    previous=''
    for item in sfx:
        x=read_wav(ROOT/item['file'])
        if x.shape[1]==1:x=np.repeat(x,2,axis=1)
        gap=.7 if item['category']!=previous else .32
        silence=np.zeros((round(gap*SR),2),np.float32)
        clips.append(silence);cursor+=len(silence)
        index.append({'time_seconds':round(cursor/SR,3),'file':item['file'],'description_zh':item['description_zh']})
        clips.append(x);cursor+=len(x);previous=item['category']
    reel=np.concatenate(clips,axis=0)
    path=ROOT/'Previews'/'ft_sfx_audition_reel.wav'
    write_wav(path,reel)
    encode_mp3(path,path.with_suffix('.mp3'))
    preview_items=[dict(file=path.relative_to(ROOT).as_posix(),category='Preview',description_zh='全部音效依次串听',variant_group='',loop=False,bpm='',key='',time_signature='',creation_method='Original masters concatenated with silence',source='Source/finish.py',listening_status='人工听感待确认')]
    (ROOT/'Previews'/'audition_index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PREVIEWS: 48-second dense battle mix',flush=True)
    duration=48.; mix=np.zeros((round(duration*SR),2),np.float32)
    bed=read_wav(ROOT/'BGM'/'ft_bgm_battle.wav')[:len(mix)].copy()
    bed*=.82
    bed[round(41*SR):]*=np.linspace(1,.15,len(bed)-round(41*SR))[:,None]
    mix+=bed
    bank=defaultdict(list)
    for item in sfx:bank[item['variant_group']].append(item)
    events=[]; counters=Counter()
    def shot(group,at,gain=.22,pan=0):
        candidates=bank[group]; item=candidates[counters[group]%len(candidates)]
        counters[group]+=1; x=read_wav(ROOT/item['file'])
        add(mix,x[:,0] if x.shape[1]==1 else x,at,gain,pan)
        events.append({'time_seconds':round(at,3),'file':item['file'],'gain':gain,'pan':pan})
    for at in [1.5,3.4,5.2]:shot('tower_build',at,.34)
    shot('round_start',7,.34)
    rng=rng_for('battle-audition-events')
    for i,at in enumerate(np.arange(8.,40.,.17)):
        dense=16<=at<=33
        if not dense and i%3:continue
        pan=float(rng.uniform(-.65,.65))
        shot('normal_fire',float(at),.16 if dense else .20,pan)
        shot('normal_hit',float(at)+.08,.11,-pan*.5)
        if i%5==0:shot(['light_hit','wing_hit','insect_hit','heavy_hit'][i%4],float(at)+.06,.14,pan)
        if i%9==0:shot(['light_death','wing_death','insect_death','heavy_death'][i%4],float(at)+.15,.18,-pan)
    for i,at in enumerate(np.arange(11,39,1.15)):
        shot('blast_fire',float(at),.27,(-1 if i%2 else 1)*.4)
        shot('blast_hit',float(at)+.29,.25,(-1 if i%2 else 1)*.2)
    for at in [13.,17.,21.,25.,29.,33.,37.]:shot('frost_loop',at,.15,-.25)
    shot('frost_activate',12.7,.25,-.25)
    for at in [16.,23.,30.,37.]:shot('frost_pulse',at,.20,-.25)
    shot('tower_upgrade',19,.27)
    shot('enemy_leak',27,.38)
    shot('low_hp',32,.35)
    shot('round_clear',40,.35)
    add(mix,read_wav(ROOT/'Stingers'/'ft_stinger_victory.wav'),42,.7)
    path=ROOT/'Previews'/'ft_dense_battle_mix.wav'
    master_music(edge(mix,.35,.5),path,-17.0)
    encode_mp3(path,path.with_suffix('.mp3'))
    preview_items.append(dict(file=path.relative_to(ROOT).as_posix(),category='Preview',description_zh='48秒密集战斗混音：多塔、敌人、提示与音乐',variant_group='',loop=False,bpm=116,key='D minor',time_signature='4/4',creation_method='Offline arrangement of original masters',source='Source/finish.py',listening_status='人工听感待确认'))
    (ROOT/'Previews'/'dense_mix_events.json').write_text(json.dumps(events,ensure_ascii=False,indent=2),encoding='utf-8')
    for item in catalog:
        if item['category']=='BGM':
            name=Path(item['file']).stem
            print(f'PREVIEWS: three-pass loop {name}',flush=True)
            subprocess.run([FFMPEG,'-v','error','-y','-stream_loop','2','-i',str(ROOT/item['file']),
                            '-codec:a','libmp3lame','-q:a','4',str(ROOT/'Previews'/f'{name}_3passes.mp3')],check=True)
    return preview_items,index


def measure_variants(catalog):
    groups=defaultdict(list)
    for item in catalog:
        if item.get('variant_group'):groups[item['variant_group']].append(item)
    result=[]
    for name,items in groups.items():
        if len(items)<2:continue
        pairs=[]
        for a,b in zip(items,items[1:]):
            x=read_wav(ROOT/a['file'])[:,0];y=read_wav(ROOT/b['file'])[:,0]
            n=min(len(x),len(y))
            corr=float(np.corrcoef(x[:n],y[:n])[0,1])
            pairs.append({'a':a['file'],'b':b['file'],'zero_lag_correlation':round(corr,5),
                          'identical_pcm':bool(len(x)==len(y) and np.array_equal(x,y))})
        result.append({'group':name,'pairs':pairs,'all_pcm_distinct':not any(p['identical_pcm'] for p in pairs)})
    return result


def waveform_svg(path):
    names=['menu','prepare','battle','pressure']
    colors=['#40d9e8','#8ecab2','#f2bc66','#f28582']
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="780" viewBox="0 0 1200 780">',
         '<rect width="1200" height="780" fill="#111d29"/>',
         '<text x="40" y="40" fill="#e4eff4" font-size="24" font-family="sans-serif">Freedom Tower — Original music / waveform overview</text>']
    for row,(name,color) in enumerate(zip(names,colors)):
        x=read_wav(ROOT/'BGM'/f'ft_bgm_{name}.wav')
        y=135+row*175
        svg.append(f'<text x="40" y="{y-55}" fill="{color}" font-size="19" font-family="sans-serif">{name.upper()} / {len(x)/SR:.2f} s</text>')
        for i,chunk in enumerate(np.array_split(x,1080)):
            p=float(np.max(np.abs(chunk)))*46
            svg.append(f'<path d="M{60+i},{y-p:.2f} V{y+p:.2f}" stroke="{color}" stroke-width="1"/>')
        for bar in [0,8,16,24,32]:
            xx=60+1080*bar/32
            svg.append(f'<path d="M{xx},{y-48} V{y+48}" stroke="#fff" stroke-opacity=".18"/>')
    svg.append('</svg>');path.write_text('\n'.join(svg),encoding='utf-8')


def documents(records,variants,index):
    masters=[r for r in records if r['category']!='Preview']
    bgm=[r for r in masters if r['category']=='BGM']
    counts=Counter(r['category'] for r in masters)
    failed=[{'file':r['file'],'checks':[k for k,v in r['checks'].items() if not v]} for r in records if not r['automated_check_pass']]
    report={'pack':'Freedom Tower — Watchlight / 守望微光','production_date':'2026-10-23 Asia/Shanghai',
            'sample_rate_hz':SR,'bit_depth':24,'master_asset_count':len(masters),'counts':dict(counts),
            'total_bgm_seconds':round(sum(r['duration_seconds'] for r in bgm),3),
            'automated_measurement':'FFmpeg loudnorm input_i/input_tp + decoded 24-bit PCM inspection',
            'loop_check':'Three complete repetitions encoded; two PCM joins analyzed per loop master',
            'human_listening':'NOT performed: this session has no audio perception tool. Playback previews are delivered for user audition.',
            'all_automated_checks_pass':not failed,'failures':failed,
            'variant_groups':variants,'assets':records}
    quality=ROOT/'Quality';quality.mkdir(exist_ok=True)
    (quality/'audio_quality_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    columns=['file','category','description_zh','duration_seconds','sample_rate_hz','bit_depth','channels','variant_group',
             'loop','loop_start_sample_frame','loop_end_sample_frame_exclusive','loop_unit','loop_start_seconds','loop_end_seconds',
             'bpm','key','time_signature','sample_peak_dbfs','true_peak_dbtp','integrated_lufs','loudness_range_lu',
             'rms_dbfs','dc_offset','stereo_correlation','mono_fold_rms_change_db','clipped_samples',
             'leading_silence_ms','trailing_silence_ms','seam_jump_dbfs','seam_neighbor_p999_dbfs',
             'automated_check_pass','creation_method','source','listening_status','file_sha256']
    with (ROOT/'asset_manifest.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,columns,extrasaction='ignore');writer.writeheader();writer.writerows(records)
    overview=['# 音频技术检查报告','',f'母版资源：{len(masters)}；试听混音 WAV：2。',
              f'自动检查：{"全部通过" if not failed else "存在待处理项"}。',
              '','这些检查验证文件和信号性质。人工听感尚未确认，不能据此声称音乐或音效已通过听感验收。','',
              '| 曲目 | 时长 | LUFS-I | 真峰值 dBTP | 循环接缝 dBFS | 单声道折叠变化 dB |',
              '|---|---:|---:|---:|---:|---:|']
    for r in bgm:overview.append(f'| {Path(r["file"]).stem} | {r["duration_seconds"]:.2f}s | {r["integrated_lufs"]} | {r["true_peak_dbtp"]} | {r["seam_jump_dbfs"]} | {r["mono_fold_rms_change_db"]} |')
    overview+=['','检查范围：48k/24bit 文件格式、非静音、削波、真峰值、DC、声道折叠、首尾样本及循环边界；音效组验证非相同 PCM。',
               '循环边界与邻近采样变化比较，并交付三遍连续循环 MP3 供试听；MP3 为有损预览，生产循环使用 WAV 母版。',
               '短音效的 LUFS-I 仅供记录，不用于跨时长的听感等响判断。',
               '噪声纹理为有意设计的合成内容；无法靠自动分析确认是否刺耳、是否符合审美或是否存在主观掩蔽。']
    if failed:overview+=['','待处理项：',json.dumps(failed,ensure_ascii=False,indent=2)]
    (quality/'QA_zh.md').write_text('\n'.join(overview),encoding='utf-8')
    waveform_svg(quality/'music_waveforms.svg')
    readme=['# Freedom Tower 原创音频包：守望微光 / Watchlight','',
      '制作日期：2026-10-23。制作工程：D:/FreedomTower_1，Unity 2022.3.62f3c1。',
      '本包为独立音频资源，尚未接入游戏。全部音频由原创音符事件、振荡器、滤波噪声及离线混音生成，没有使用第三方录音、采样包或现成旋律。',
      '',f'交付：4 首循环音乐、3 段结算短曲、{sum(v for k,v in counts.items() if k.startswith("SFX"))} 个音效 WAV，合计 {len(masters)} 个母版；另含 2 个试听混音 WAV。',
      '全部 WAV 为 48 kHz / 24-bit PCM；音乐和短曲为立体声，音效为单声道。',
      '','## 风格与音乐结构','',
      '主题“守望微光”使用 D–F–A–G–E / D–C–A 的轮廓，配合有节奏的机械拨弦、柔和合成垫底、晶体钟音和克制打击乐。四首共用主题身份，分别表达菜单、布阵、常规战斗和高压防守。',
      '每首 32 小节，分为主题陈述、编配扩展、对比段、主题回归四部分；和弦、低音、分解音型与乐句有段落变化。',
      '','| 曲目 | BPM | 调式 | 时长 | 循环 |','|---|---:|---|---:|---|']
    for r in bgm:readme.append(f'| [{Path(r["file"]).stem}]({r["file"]}) | {r["bpm"]} | {r["key"]} | {r["duration_seconds"]:.2f}s | 整个 WAV；0 到 {r["sample_frames"]} 样本帧，末端不含 |')
    readme+=['','## 试听','',
      '- 打开 [试听页面](LISTEN.html)，可播放曲目和所有音效。',
      '- [48 秒密集战斗混音](Previews/ft_dense_battle_mix.mp3)：音乐、多塔开火、爆炸、冰晶光环、敌人及提示。',
      '- [全部音效串听](Previews/ft_sfx_audition_reel.mp3)：各文件之间有静音间隔，索引见下表与 Previews/audition_index.json。',
      '- 四首 *_3passes.mp3 为三遍连续循环试听。WAV 是生产母版，MP3 仅供预览。',
      '','## 验证状态','',
      '已制作：全部母版、音效变体、MIDI/音符事件、试听文件。',
      f'已分析：{len(records)} 个 WAV 的格式、信号与循环边界，结果见 Quality/QA_zh.md、Quality/audio_quality_report.json 和 asset_manifest.csv。',
      '已试听：本执行环境未提供音频感知能力，因此未进行人工听感验收。最终的音乐审美、刺耳程度、混音掩蔽和反复播放疲劳仍需通过所附预览确认。',
      '','## 文件与复现','',
      'BGM/、Stingers/、SFX/ 为母版；Previews/ 为试听；Source/ 为合成代码、逐音符编曲 JSON、MIDI 和依赖列表。MIDI 的 GM 音色仅供编辑互换，精确复现使用自带 Python 合成器。',
      '运行命令（在该目录中）：',
      '```powershell','python -m pip install -r Source/requirements.txt',
      'python Source/produce.py','python Source/finish.py','```',
      '每个事件以 SHA256 派生固定随机种子；源脚本在固定依赖环境可复现音符、噪声与音色。',
      'Source/.dependencies 为本机工具安装缓存，不进入交付 ZIP；Source/_work 为临时测量目录，也不进入 ZIP。',
      '声音设计中有意使用滤波噪声作为机械、爆破、虫壳和气流纹理。生物声音为风格化合成，不是真实动物录音。',
      '','## 音效串听时间索引','', '| 时间 | 文件 | 内容 |','|---|---|---|']
    for e in index:
        t=e['time_seconds'];readme.append(f'| {int(t//60):02d}:{t%60:05.2f} | {Path(e["file"]).name} | {e["description_zh"]} |')
    (ROOT/'README_zh.md').write_text('\n'.join(readme)+'\n',encoding='utf-8')
    version=subprocess.run([FFMPEG,'-version'],capture_output=True,text=True,check=True).stdout
    provenance={'audio_sources':'No third-party audio samples, recordings, soundfonts, convolution IRs, or stock compositions.',
                'composition':'Original event score authored in Source/produce.py, theme Watchlight.',
                'synthesis':'Original DSP code in Source/synthesis.py and Source/produce.py.',
                'tools':{'Python':platform.python_version(),'NumPy':np.__version__,
                         'SciPy':__import__('scipy').__version__,'mido':'1.3.3','imageio-ffmpeg':'0.6.0','FFmpeg':version},
                'license_note':'Tool dependencies are not audio sources. Their tool binaries are not redistributed in the ZIP. Retain upstream licenses when separately installing tools.',
                'render_engine':'Custom additive/FM-like instruments, filtered-noise synthesis, envelope design, deterministic random variations, sparse synthetic ambience.',
                'auditory_review':'Pending human audition; no claim of auditory approval.'}
    (HERE/'provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'SOURCES_AND_LICENSES_zh.md').write_text('''# 制作来源与工具说明

音频内容：本包从原创音符事件、数学振荡器和确定性随机噪声生成。未使用第三方音频采样、真实录音、现成旋律、SoundFont 或卷积混响 IR。

制作代码与编曲：Source/synthesis.py、Source/produce.py；处理与测量：Source/finish.py。

工具：Python（PSF）、NumPy / SciPy（BSD 系列许可）、mido（MIT）、imageio-ffmpeg（BSD）、FFmpeg（实际构建配置见 Source/provenance.json，包含 libmp3lame 等）。这些是制作工具，不是声音素材。交付 ZIP 不包含工具二进制及安装缓存；工具本身的再分发须遵循各自上游许可。

本包中提供的脚本、音符事件、MIDI 和音频作为本次委托成果交付，可用于本游戏的编辑与后续制作。

固定种子与所有参数在源代码中；具体依赖版本见 Source/requirements.txt。精确波形请使用同样工具版本与渲染方式。
''',encoding='utf-8')
    cards=[]
    for category in ['BGM','Stinger','Preview','SFX/UI','SFX/Tower','SFX/Enemy','SFX/Feedback']:
        group=[r for r in records if r['category']==category]
        cards.append(f'<h2>{html.escape(category)}</h2><div class="grid">')
        for r in group:
            file=r['file']
            source=f'Previews/{Path(file).stem}.mp3' if category in ('BGM','Stinger') else str(Path(file).with_suffix('.mp3')).replace('\\','/') if category=='Preview' else file
            cards.append(f'<article><b>{html.escape(r["description_zh"])}</b><small>{html.escape(Path(file).name)} · {r["duration_seconds"]:.2f}s</small><audio controls preload="none" src="{html.escape(source)}"></audio><a href="{html.escape(file)}" download>WAV 母版</a></article>')
        cards.append('</div>')
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Freedom Tower · 守望微光</title><style>
body{margin:0;background:#111b27;color:#e5edf6;font:16px/1.6 system-ui,sans-serif}main{max-width:1300px;margin:auto;padding:36px 24px}h1{font-size:36px;color:#56d8ee;margin-bottom:8px}h2{border-bottom:1px solid #294c62;padding:24px 0 8px}.intro{color:#b4c5d6;max-width:860px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:15px}article{background:#1a2939;border:1px solid #2c485d;border-radius:10px;padding:18px}small{display:block;color:#91aabd;overflow-wrap:anywhere;margin:6px 0}audio{width:100%;margin:10px 0}a{color:#74d2df}b{font-size:17px}.tag{display:inline-block;padding:5px 10px;border:1px solid #416c7a;margin:5px 8px 5px 0;border-radius:6px;color:#9cdee9}</style><main>
<h1>守望微光 · Watchlight</h1><p class="intro">Freedom Tower 原创音乐与音效。机械科技、冰晶能量与风格化生物。四首音乐使用同一主题动机，保留布阵与观察的空间。</p><p><span class="tag">48 kHz / 24-bit WAV</span><span class="tag">4 首循环音乐</span><span class="tag">3 段短曲</span><span class="tag">独立音效与变体</span></p><p class="intro">可在此逐项试听。文件与信号分析已完成，人工听感尚待确认。<a href="README_zh.md">说明与串听索引</a> · <a href="asset_manifest.csv">资源清单</a> · <a href="Quality/QA_zh.md">技术检查</a></p>'''+''.join(cards)+'</main><script>document.addEventListener("play",e=>{if(e.target.tagName==="AUDIO")document.querySelectorAll("audio").forEach(a=>{if(a!==e.target)a.pause()})},true)</script></html>'
    (ROOT/'LISTEN.html').write_text(page,encoding='utf-8')
    # Do not include dependency binaries, runtime caches, work files, or the ZIP itself.
    archive=ROOT/'FreedomTower_Watchlight_OriginalPack_20261023.zip'
    files=[p for p in ROOT.rglob('*') if p.is_file() and p!=archive and not any(s in p.parts for s in ['.dependencies','__pycache__','_work'])]
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as out:
        for p in sorted(files):out.write(p,p.relative_to(ROOT))
    print(json.dumps({'masters':len(masters),'counts':dict(counts),'wav_checked':len(records),'failures':failed,'archive_mb':round(archive.stat().st_size/1048576,2)},ensure_ascii=False),flush=True)


def main():
    catalog=json.loads((HERE/'production_catalog.json').read_text(encoding='utf-8'))
    if '--reuse-previews' in sys.argv:
        index=json.loads((ROOT/'Previews'/'audition_index.json').read_text(encoding='utf-8'))
        preview_items=[dict(file=f'Previews/{name}.wav',category='Preview',description_zh=description,
                            variant_group='',loop=False,bpm='',key='',time_signature='',
                            creation_method='Offline arrangement of original masters',source='Source/finish.py',listening_status='人工听感待确认')
                       for name,description in [('ft_sfx_audition_reel','全部音效依次串听'),('ft_dense_battle_mix','48秒密集战斗混音：多塔、敌人、提示与音乐')]]
        print('REUSING rendered preview files',flush=True)
    else:
        preview_items,index=make_previews(catalog)
    records=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for i,record in enumerate(pool.map(measure,catalog+preview_items),1):
            records.append(record)
            if i%12==0 or record['category']=='BGM':print(f'MEASURED {i}/{len(catalog)+len(preview_items)}: {record["file"]}',flush=True)
    variants=native(measure_variants(catalog))
    documents(records,variants,index)


if __name__=='__main__':main()
