"""Publish only successful actual runtime media, and prepare visual review strips."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,sys,subprocess,hashlib
HERE=Path(__file__).resolve().parent
name=sys.argv[1];directory=HERE/name
runtime=[]
for revision in ['runtime_r02','runtime_updeath_r01']:
    path=directory/revision
    if (path/'exception.txt').exists():raise ValueError('Preserved runtime exception: '+str(path))
    checks=(path/'actual_runtime_checks.txt').read_text(encoding='utf-8')
    if 'FAIL ' in checks:raise ValueError('Runtime assertions failed: '+str(path))
    records=[json.loads(line) for line in (path/'actual_frames.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    if any(b['frame']<=a['frame'] for a,b in zip(records,records[1:])):raise ValueError('Nonincreasing Unity frame records')
    if not (path/'media_manifest.json').exists():subprocess.run([sys.executable,str(HERE/'build_runtime_media.py'),name,revision],check=True)
    runtime.append({'revision':revision,'pass':checks.count('PASS '),'fail':checks.count('FAIL '),'frames':len(records),'records_sha256':hashlib.sha256((path/'actual_frames.jsonl').read_bytes()).hexdigest().upper()})
first=[json.loads(line) for line in (directory/'runtime_r02/actual_frames.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
second=[json.loads(line) for line in (directory/'runtime_updeath_r01/actual_frames.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
canvas=Image.new('RGB',(1800,1000),(40,48,37));draw=ImageDraw.Draw(canvas)
sources=[]
for row,(records,revision,stage) in enumerate([(first,'runtime_r02','UpWalk'),(first,'runtime_r02','DownWalk'),(first,'runtime_r02','Attack'),(second,'runtime_updeath_r01','DeathAutoRecycle')]):
    subset=[r for r in records if r['stage']==stage]
    if not subset:raise ValueError('No actual visual evidence for '+stage)
    for i in range(6):
        r=subset[round((len(subset)-1)*i/5)];im=Image.open(directory/revision/r['file']).convert('RGB');im=im.resize((250,250),Image.Resampling.LANCZOS)
        canvas.paste(im,(i*300+25,row*250));draw.text((i*300+5,row*250+8),stage+' '+r['facing']+' f'+str(r['frame']),fill='white')
        sources.append({'revision':revision,'file':r['file'],'frame':r['frame']})
canvas.save(directory/'runtime_visual_strip.png')
(directory/'runtime_summary.json').write_text(json.dumps({'name':name,'runtime':runtime,'passes':sum(x['pass'] for x in runtime),'failures':0,'actual_frames':sum(x['frames'] for x in runtime),'visual_strip_sources':sources,'status':'runtime_complete_pending_visual_check'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'name':name,'runtime':runtime,'visual_strip':str(directory/'runtime_visual_strip.png')}))
