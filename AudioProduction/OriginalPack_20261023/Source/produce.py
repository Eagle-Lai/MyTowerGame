"""Compose and render the original pack. Run with Python 3.12 + requirements.txt."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from synthesis import *
import mido

ROOT = HERE.parent
ASSETS = []


def register(path,category,description,group='',loop=False,bpm='',key='',extra=None):
    item={'file':Path(path).relative_to(ROOT).as_posix(),'category':category,
          'description_zh':description,'variant_group':group,'loop':loop,'bpm':bpm,
          'key':key,'time_signature':'4/4' if bpm else '',
          'creation_method':'Original offline composition / procedural synthesis',
          'source':'Source/produce.py; Source/synthesis.py; seed = SHA256(event key)',
          'listening_status':'人工听感待确认（当前环境未提供音频感知工具）'}
    if extra:item.update(extra)
    ASSETS.append(item)


TRACKS = {
 'menu':dict(bpm=96,key='D Dorian / D minor',description='青蓝守望：菜单主题',energy=.52),
 'prepare':dict(bpm=88,key='D Dorian',description='布阵微光：战前规划',energy=.30),
 'battle':dict(bpm=116,key='D natural minor',description='机械守线：常规防守',energy=.78),
 'pressure':dict(bpm=128,key='D minor with harmonic-minor dominant',description='钢与冰：高压防守',energy=1.),
}


def create_score(name,config):
    bpm=config['bpm']; beat=60/bpm
    score=[]
    def note(track,kind,pitch,on,duration,gain,pan=0):
        score.append(dict(track=track,kind=kind,note=int(pitch),beat=round(on,6),
                          duration_beats=duration,gain=gain,pan=pan))
    def drum(kind,on,gain,pan=0):
        score.append(dict(track='drums',kind=kind,note=None,beat=on,duration_beats=0,gain=gain,pan=pan))
    if name in ('menu','prepare'):
        chords=[[50,57,60,64],[43+12,59,62,64],[48,55,59,62],[45,52,55,62]]
        roots=[38,43,36,45]
    else:
        chords=[[50,57,60,64],[46,53,57,60],[53,57,60,67],[48,55,58,62]]
        roots=[38,34,41,36]
    motif=[(0,74,.65),(.75,77,.50),(1.5,81,.8),(2.5,79,.42),
           (3.25,76,.5),(4,74,.8),(5.25,72,.5),(6,69,1.55)]
    response=[(0,69,.7),(1,72,.6),(1.75,74,.8),(3,77,.55),
              (4,76,.7),(5,74,.65),(6,72,.6),(7,69,.6)]
    for bar in range(32):
        part=bar//8; within=bar%8; on=bar*4
        idx=(bar//2)%4
        chord=chords[idx]; root=roots[idx]
        if part==2:
            bridge=[[43+12,58,62,65],[46,53,57,60],[50,57,60,64],[45,52,57,61]]
            chord=bridge[idx]; root=[43,34,38,33][idx]
        energy=config['energy']*(.72 if part==0 else .82 if part==2 else 1.)
        for j,pitch in enumerate(chord):
            note('pad','pad',pitch,on,3.85,.085*(.8 if name=='pressure' else 1),[-.55,.4,-.25,.6][j])
        bass_pattern=[(0,1.65),(2,.95)] if name in ('menu','prepare') else [(0,.65),(1.5,.42),(2,.65),(3.25,.4)]
        if name=='prepare':bass_pattern=[(0,2.5)]
        for b,d in bass_pattern:
            note('bass','bass',root,on+b,d,.22*(.75 if name=='prepare' else 1))
        # Articulated ostinati shift register, rhythm, and inversion across sections.
        arp_step=1.0 if name=='prepare' else .5
        if name=='menu' and part==2:arp_step=1.
        if name=='pressure' and within in (3,7):arp_step=.25
        for k,b in enumerate(np.arange(.25 if name=='prepare' else 0,3.99,arp_step)):
            pitch=chord[(k+bar//4)%4]+(12 if name in ('menu','prepare') else 0)
            if (k+bar)%7==0:pitch+=12
            note('arpeggio','pluck',pitch,on+float(b),.30 if name!='prepare' else .6,
                 .095*(.8 if name=='prepare' else 1)*(1 if k%2==0 else .77),-.42 if k%2==0 else .42)
        # Theme is stated in two-bar phrases, with rests and a contrasting bridge.
        has_theme=(bar%2==0 and ((name=='menu' and part!=2 and within>=2)
                    or (name=='prepare' and part in (1,3) and within in (2,6))
                    or (name in ('battle','pressure') and part!=2 and within in (0,4))))
        if has_theme:
            phrase=motif if (bar//4)%2==0 else response
            for b,pitch,d in phrase:
                if name=='prepare':pitch-=12
                note('theme','lead' if name in ('battle','pressure') else 'bell',pitch,on+b,d,
                     .19 if name in ('battle','pressure') else .16,.08)
        if part==2 and bar%2==0:
            for k,p in enumerate([chord[1]+12,chord[2]+12,chord[0]+12]):
                note('countermelody','bell',p,on+.5+2*k,1.1,.12,[-.45,.35,0][k])
        if name=='prepare':
            if bar%2==0:drum('shaker',on+2,.035,-.35)
            if part==3:drum('tom',on,.065)
        else:
            for b in ([0,2] if name=='menu' else [0,1.75,2,3.5] if name=='pressure' else [0,2,2.75]):
                drum('kick',on+b,.19*energy)
            for b in ([3] if name=='menu' else [1,3]):
                drum('snare',on+b,.15*energy,-.08)
            step=1. if name=='menu' else .5
            for k,b in enumerate(np.arange(.5,4,step)):
                drum('hat',on+float(b),.065*energy*(.65 if k%2 else 1),.36)
            if within==7:
                drum('tom',on+3.25,.13*energy,-.3)
                drum('tom',on+3.75,.11*energy,.3)
            if name=='pressure' and part in (1,3):
                for b in [.25,1.25,2.25,3.25]:drum('shaker',on+b,.036,-.4)
    return dict(name=f'ft_bgm_{name}',bpm=bpm,key=config['key'],bars=32,
                time_signature='4/4',theme_name='Watchlight / 守望微光',
                structure=['A: restrained statement, bars 1–8','A2: fuller theme, bars 9–16',
                           'B: contrasting bridge, bars 17–24','A3: theme return, bars 25–32'],
                events=score)


def save_midi(score,path):
    mid=mido.MidiFile(ticks_per_beat=480)
    tempo=mido.MidiTrack(); mid.tracks.append(tempo)
    tempo.append(mido.MetaMessage('set_tempo',tempo=mido.bpm2tempo(score['bpm']),time=0))
    tempo.append(mido.MetaMessage('time_signature',numerator=4,denominator=4,time=0))
    programs={'pad':89,'bass':38,'arpeggio':10,'theme':80,'countermelody':14}
    drums={'kick':36,'snare':38,'hat':42,'openhat':46,'tom':45,'shaker':70}
    for ch,track_name in enumerate(sorted(set(e['track'] for e in score['events']))):
        tr=mido.MidiTrack(); mid.tracks.append(tr)
        tr.append(mido.MetaMessage('track_name',name=track_name,time=0))
        channel=9 if track_name=='drums' else ch
        if channel!=9:tr.append(mido.Message('program_change',program=programs[track_name],channel=channel,time=0))
        events=[]
        for e in score['events']:
            if e['track']!=track_name:continue
            pitch=drums[e['kind']] if e['note'] is None else e['note']
            start=round(e['beat']*480); end=round((e['beat']+max(.12,e['duration_beats']))*480)
            velocity=int(np.clip(e['gain']*400,20,115))
            events.extend([(start,1,pitch,velocity),(end,0,pitch,0)])
        previous=0
        for tick,on,pitch,velocity in sorted(events):
            tr.append(mido.Message('note_on' if on else 'note_off',channel=channel,note=pitch,velocity=velocity,time=tick-previous))
            previous=tick
    path.parent.mkdir(parents=True,exist_ok=True); mid.save(path)


def music():
    for name,config in TRACKS.items():
        print(f'COMPOSE {name}',flush=True)
        score=create_score(name,config); beat=60/score['bpm']
        n=round(score['bars']*4*beat*SR)
        dry=np.zeros((n,2),np.float32); melodic=np.zeros_like(dry)
        for i,e in enumerate(score['events']):
            if e['note'] is None:
                y=percussion(e['kind'],key=f'{name}:{i}')
                add(dry,y,e['beat']*beat,e['gain'],e['pan'],True)
            else:
                y=instrument(e['kind'],e['note'],e['duration_beats']*beat,key=f'{name}:{i}')
                add(melodic,y,e['beat']*beat,e['gain'],e['pan'],True)
        melodic=ambience(melodic,.32 if name=='prepare' else .23,True)
        dry+=melodic
        path=ROOT/'BGM'/f'ft_bgm_{name}.wav'
        mastering=master_music(dry,path,-17.3 if name!='pressure' else -17.0)
        score['render_mastering']=mastering
        score['loop_start_sample_frame']=0; score['loop_end_sample_frame_exclusive']=n
        (HERE/'Scores').mkdir(exist_ok=True)
        (HERE/'Scores'/f'ft_bgm_{name}.json').write_text(json.dumps(score,ensure_ascii=False,indent=2),encoding='utf-8')
        save_midi(score,HERE/'MIDI'/f'ft_bgm_{name}.mid')
        register(path,'BGM',config['description'],loop=True,bpm=score['bpm'],key=score['key'])
        encode_mp3(path,ROOT/'Previews'/f'ft_bgm_{name}.mp3')
        print(f'RENDERED {path.name}: {n/SR:.2f}s / {len(score["events"])} events',flush=True)


def stingers():
    specs={
        'victory':(5.6,[(0,[62,69,74],.8),(.5,[65,72,77],.8),(1.,[69,74,81],.9),(1.65,[62,66,69,74,78],2.8)]),
        'defeat':(4.5,[(0,[62,65,69],1.),(.8,[60,64,67],1.),(1.65,[50,57,60,64],2.1)]),
        'rating':(2.4,[(0,[74],.35),(.16,[77],.35),(.32,[81],.35),(.60,[74,78,81,86],1.)]),
    }
    for name,(duration,notes) in specs.items():
        x=np.zeros((round(duration*SR),2),np.float32)
        score=dict(name=f'ft_stinger_{name}',bpm=120,events=[])
        for i,(at,chord,held) in enumerate(notes):
            for j,pitch in enumerate(chord):
                add(x,instrument('bell' if name=='rating' else 'lead',pitch,held,key=f'{name}:{i}:{j}'),at,.20/np.sqrt(len(chord)),(j-(len(chord)-1)/2)*.2)
                add(x,instrument('pad',pitch-12,held,key=name),at,.09/np.sqrt(len(chord)),0)
                score['events'].append(dict(track='theme',kind='lead',note=pitch,beat=at*2,duration_beats=held*2,gain=.2,pan=0))
        if name=='victory':
            add(x,percussion('tom',key=name),0,.16,-.2)
            add(x,percussion('kick',key=name),1.65,.2)
        x=ambience(x,.4)
        path=ROOT/'Stingers'/f'ft_stinger_{name}.wav'
        master_music(edge(x,.005,.35),path,-17.5)
        register(path,'Stinger',{'victory':'胜利：主题上行与大调收束','defeat':'失败：下行主题与温和小调收束','rating':'评级完成：晶体音阶与明亮和弦'}[name],bpm=120,key='D major resolution' if name!='defeat' else 'D minor')
        (HERE/'Scores'/f'ft_stinger_{name}.json').write_text(json.dumps(score,ensure_ascii=False,indent=2),encoding='utf-8')
        save_midi(score,HERE/'MIDI'/f'ft_stinger_{name}.mid')
        encode_mp3(path,ROOT/'Previews'/f'ft_stinger_{name}.mp3')
        print(f'RENDERED {path.name}',flush=True)


def tone(freq,duration,decay=15,amp=1.,vibrato=0):
    t=clock(duration)
    return edge(amp*np.sin(2*np.pi*freq*t + vibrato*np.sin(2*np.pi*19*t))*np.exp(-t*decay),.002,.02)


def sweep(start,end,duration,decay=10):
    t=clock(duration)
    phase=2*np.pi*(start*t+(end-start)*t*t/(2*duration))
    return edge(np.sin(phase)*np.exp(-t*decay),.002,.025)


def effect(kind,index):
    rng=rng_for(f'ft-sfx-20261023:{kind}:{index}')
    vary=float(rng.uniform(.93,1.08)); v=index%3
    lengths={'ui_click':.13,'ui_confirm':.25,'ui_back':.2,'ui_invalid':.23,'ui_toggle':.14,
      'tower_select':.24,'tower_build':.64,'tower_build_fail':.32,'tower_upgrade':.95,'tower_sell':.67,
      'normal_fire':.23,'normal_hit':.18,'blast_fire':.44,'blast_hit':1.0,
      'frost_activate':.95,'frost_pulse':.62,'frost_loop':4.0,
      'light_hit':.22,'light_death':.47,'wing_hit':.25,'wing_death':.55,
      'insect_hit':.23,'insect_death':.51,'heavy_hit':.40,'heavy_death':.95,
      'round_start':.75,'round_clear':.85,'enemy_leak':.46,'low_hp':.70,
      'pause':.26,'resume':.28,'speed_change':.24}
    duration=lengths[kind]*(1 if kind=='frost_loop' else vary)
    x=np.zeros(round(duration*SR),np.float32)
    def put(y,at=0,gain=1):add(x,y,at,gain)
    def noise(dur,lo=120,hi=6000,decay=18):
        t=clock(dur)
        return edge(filtered(rng.normal(size=len(t)),low=lo,high=hi)*np.exp(-t*decay),.001,.02)
    def modes(freqs,dur,decay,at=0,gain=1):
        for j,f in enumerate(freqs):put(tone(f*vary,dur,decay*(1+j*.16),1/(j+1)),at,gain)
    if kind.startswith('ui_'):
        if kind=='ui_click':
            modes([930+v*75,1870,2810],duration,60,gain=.42)
            put(noise(.035,900,4500,130),gain=.11)
        elif kind=='ui_confirm':
            modes([587.33,1174.66],.18,22,gain=.35)
            modes([880,1760],.17,24,at=.075,gain=.32)
        elif kind=='ui_back':
            put(sweep(740,460,.16,18),gain=.34)
            put(noise(.055,400,2200,70),gain=.08)
        elif kind=='ui_invalid':
            modes([246.94,310.],.14,25,gain=.32)
            modes([220,277],.13,30,at=.08,gain=.28)
        else:
            modes([1174.66,1762.],.10,50,gain=.35)
            put(tone(620,.045,60),.035,.17)
    elif kind=='tower_select':
        modes([390,780,1565],.18,32,gain=.3)
        modes([587,1174],.15,24,at=.055,gain=.2)
    elif kind=='tower_build':
        put(noise(.13,90,1600,28),gain=.6)
        put(sweep(145,72,.22,15),gain=.7)
        for at in [.055,.12,.19]:modes([730+v*30,1510,2430],.20,29,at,gain=.15)
        put(instrument('bell',74,.22,key=f'build{v}'),.24,.22)
    elif kind=='tower_build_fail':
        put(noise(.12,200,1700,35),gain=.3)
        modes([196,233],.20,17,gain=.35)
        put(tone(146.8,.17,20),.10,.22)
    elif kind=='tower_upgrade':
        put(noise(.4,350,4800,9),gain=.16)
        for j,p in enumerate([62,65,69,74]):put(instrument('bell',p,.32,key=str(v)),.1*j,.3)
        modes([1174,2349],.45,10,at=.38,gain=.17)
        put(tone(110,.3,14),.25,.18)
    elif kind=='tower_sell':
        for j,f in enumerate([1560,1160,780]):modes([f,f*1.42],.17,25,.06*j,gain=.19)
        put(noise(.3,180,1800,13),.08,.35)
        modes([1760,2641],.28,18,.3,gain=.18)
    elif kind=='normal_fire':
        put(noise(.065,500+v*130,5200-v*200,52),gain=.65)
        put(sweep(215+v*18,95,.095,29),gain=.65)
        modes([1040+v*135,2240],.10,39,.018,gain=.11)
        put(noise(.07,300,2400,48),.08,.13)
    elif kind=='normal_hit':
        put(noise(.095,800,6500,42),gain=.48)
        modes([610+v*90,1490,2700],.12,38,gain=.18)
    elif kind=='blast_fire':
        put(sweep(155+v*12,48,.27,13),gain=.9)
        put(noise(.23,70,3300,19),gain=.8)
        modes([410,830,1730],.22,22,.018,gain=.20)
        put(noise(.16,160,1700,22),.12,.20)
    elif kind=='blast_hit':
        put(sweep(130,38,.55,8),gain=.85)
        put(noise(.63,60,4700-v*350,8),gain=.95)
        put(noise(.42,300,1800,9),.08,.36)
        for j in range(6):
            at=.10+j*.065+rng.uniform(0,.015)
            modes([rng.uniform(560,1300),rng.uniform(1800,2800)],.18,32,at,gain=.09)
    elif kind in ('frost_activate','frost_pulse'):
        base=74 if kind=='frost_activate' else 81
        for j,offset in enumerate([0,7,12,19]):
            put(instrument('bell',base+offset,.33 if kind=='frost_activate' else .18,key=f'{kind}{v}{j}'),j*.055,.30/(1+j*.45))
        put(noise(duration*.65,1700,9000,8),gain=.17)
        put(sweep(320,700,duration*.65,7),gain=.12)
    elif kind=='frost_loop':
        t=clock(duration)
        # Integer-cycle oscillators and modulators produce an exact periodic field.
        for f,a in [(293.75,.24),(440.,.13),(587.25,.10),(880.,.04),(1174.5,.025)]:
            x += (a*np.sin(2*np.pi*f*t)*(1+.16*np.sin(2*np.pi*.5*t))).astype(np.float32)
        x += (.018*np.sin(2*np.pi*1761*t)*np.sin(2*np.pi*.75*t)).astype(np.float32)
    elif kind.endswith('_hit') or kind.endswith('_death'):
        family=kind.split('_')[0]; death=kind.endswith('death')
        if family=='light':
            put(sweep(570+v*70,180 if death else 370,duration*.9,8 if death else 21),gain=.38)
            put(noise(duration*.85,650,3900,11 if death else 27),gain=.25)
            if death:put(sweep(330,120,.22,12),.12,.22)
        elif family=='wing':
            for j in range(3 if death else 2):
                at=j*.065
                put(sweep(1500+v*140,680,.13,20),at,.24)
                put(noise(.11,850,5000,26),at,.22)
        elif family=='insect':
            for j in range(5 if death else 3):
                at=j*(.055 if death else .027)
                modes([1350+v*170,2240,3910],.075,55,at,gain=.24)
                put(noise(.055,1600,6900,70),at,.16)
            if death:put(noise(.25,400,2200,15),.15,.25)
        else:
            t=clock(duration*.9)
            base=(92+v*9)*(1-.45*t/max(t))
            phase=2*np.pi*np.cumsum(base)/SR
            carrier=np.sin(phase+1.1*np.sin(phase*.51))+.24*np.sin(phase*2)
            formant=(1+.2*np.sin(2*np.pi*(23+v*3)*t))
            put(edge(carrier*formant*np.exp(-t*(4 if death else 12)),.009,.10),gain=.52)
            put(noise(duration*.75,130,1800,6 if death else 19),gain=.35)
    elif kind in ('round_start','round_clear'):
        notes=[62,69,74] if kind=='round_start' else [74,77,81]
        for j,p in enumerate(notes):put(instrument('pluck' if kind=='round_start' else 'bell',p,.26,key=str(v)),.12*j,.35)
        put(tone(146.83,.2,18),gain=.18)
    elif kind=='enemy_leak':
        put(sweep(620,270,.30,7),gain=.4)
        put(noise(.17,180,2300,18),gain=.18)
        modes([196,392],.24,12,.15,gain=.24)
    elif kind=='low_hp':
        for at in [0,.25]:
            modes([440,660],.17,20,at,gain=.28)
            put(tone(110,.17,20),at,.20)
    elif kind in ('pause','resume'):
        seq=[740,587] if kind=='pause' else [587,740]
        for j,f in enumerate(seq):modes([f,f*2],.14,24,.07*j,gain=.28)
    elif kind=='speed_change':
        for j in range(2+v):
            modes([587.33*2**(j*2/12)],.08,33,.037*j,gain=.28)
    else:raise ValueError(kind)
    if kind not in ('frost_loop','normal_fire','normal_hit','blast_fire','blast_hit'):
        x=ambience(x,.12)
    peak=-9 if kind.startswith('ui_') else -13 if kind=='frost_loop' else -5 if kind.startswith('blast') else -7
    return master_sfx(x,peak,kind=='frost_loop')


SFX = {
 'UI': [('ui_click',3,'轻点击'),('ui_confirm',2,'确认'),('ui_back',2,'返回或关闭'),('ui_invalid',2,'无效操作'),('ui_toggle',3,'切换选项')],
 'Tower': [('tower_select',3,'选中防御塔'),('tower_build',3,'建造成功：装配落地'),('tower_build_fail',2,'建造失败'),
           ('tower_upgrade',3,'升级：能量提升'),('tower_sell',3,'出售：拆卸与回收'),
           ('normal_fire',4,'普通塔：机械开火'),('normal_hit',3,'普通塔：轻量命中'),
           ('blast_fire',3,'爆破塔：厚重开火'),('blast_hit',3,'爆破塔：爆炸命中'),
           ('frost_activate',3,'冰霜塔：冰晶激活'),('frost_pulse',3,'冰霜塔：柔和能量脉冲'),('frost_loop',1,'冰霜塔：持续范围减速光环')],
 'Enemy': [('light_hit',3,'轻型生物受击'),('light_death',3,'轻型生物死亡'),('wing_hit',3,'鸟或蝙蝠受击'),('wing_death',3,'鸟或蝙蝠死亡'),
           ('insect_hit',3,'虫或蝎受击'),('insect_death',3,'虫或蝎死亡'),('heavy_hit',3,'重型生物受击'),('heavy_death',3,'重型生物死亡')],
 'Feedback': [('round_start',2,'回合开始'),('round_clear',2,'回合完成'),('enemy_leak',3,'敌人漏过终点'),('low_hp',2,'低生命提示'),
              ('pause',2,'暂停'),('resume',2,'继续'),('speed_change',3,'倍速切换')],
}


def sfx():
    for category,specs in SFX.items():
        for name,count,description in specs:
            for i in range(1,count+1):
                x=effect(name,i)
                path=ROOT/'SFX'/category/f'ft_sfx_{name}_{i:02d}.wav'
                write_wav(path,x)
                register(path,f'SFX/{category}',description,name,loop=name=='frost_loop')
        print(f'RENDERED SFX/{category}',flush=True)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--only',choices=['music','stingers','sfx','all'],default='all')
    args=parser.parse_args()
    if args.only in ('all','music'):music()
    if args.only in ('all','stingers'):stingers()
    if args.only in ('all','sfx'):sfx()
    metadata=HERE/'production_catalog.json'
    if args.only!='all' and metadata.exists():
        old=json.loads(metadata.read_text(encoding='utf-8'))
        newfiles={a['file'] for a in ASSETS}
        ASSETS[:]=[a for a in old if a['file'] not in newfiles]+ASSETS
    metadata.write_text(json.dumps(ASSETS,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'CATALOG: {len(ASSETS)} master assets',flush=True)


if __name__=='__main__':main()
