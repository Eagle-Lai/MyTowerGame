from session_winterwarg import *
from audit_current import audit
from PIL import Image
from collections import deque
import numpy as np
owner()
tag=sys.argv[1] if len(sys.argv)>1 else ''
assert not (D/'installed_manifest.json').exists()
report=audit();assert report['pass'] and not report['changes'],report
write(D/('scope_preinstall_20261029'+tag+'.json'),report,True)
art=D/'staged_art';metrics=[]
for p in sorted(art.glob('*.png')):
    if p.name==NAME+'_Directions.png':continue
    im=Image.open(p).convert('RGBA');a=np.asarray(im);mask=a[:,:,3]>127
    seen=np.zeros(mask.shape,dtype=bool);components=[]
    for y,x in zip(*np.where(mask)):
        if seen[y,x]:continue
        todo=[(y,x)];seen[y,x]=True;count=0
        while todo:
            yy,xx=todo.pop();count+=1
            for ry,rx in [(yy-1,xx),(yy+1,xx),(yy,xx-1),(yy,xx+1)]:
                if 0<=ry<mask.shape[0] and 0<=rx<mask.shape[1] and mask[ry,rx] and not seen[ry,rx]:seen[ry,rx]=True;todo.append((ry,rx))
        components.append(count)
    # Enclosed transparent area detects color removal that punched out an organ.
    outside=np.zeros(mask.shape,dtype=bool);q=deque()
    for y in range(mask.shape[0]):
        for x in [0,mask.shape[1]-1]:
            if not mask[y,x] and not outside[y,x]:outside[y,x]=True;q.append((y,x))
    for x in range(mask.shape[1]):
        for y in [0,mask.shape[0]-1]:
            if not mask[y,x] and not outside[y,x]:outside[y,x]=True;q.append((y,x))
    while q:
        y,x=q.popleft()
        for yy,xx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]:
            if 0<=yy<mask.shape[0] and 0<=xx<mask.shape[1] and not mask[yy,xx] and not outside[yy,xx]:outside[yy,xx]=True;q.append((yy,xx))
    entry={'file':p.name,'size':list(im.size),'sha256':sha(p),'opaque_pixels':int(mask.sum()),'components':sorted(components,reverse=True),'enclosed_transparent_pixels':int((~mask & ~outside).sum()),'magenta_opaque_pixels':int(((a[:,:,0]>200)&(a[:,:,2]>200)&(a[:,:,1]<80)&mask).sum())}
    assert entry['opaque_pixels']>50 and entry['magenta_opaque_pixels']==0,entry
    metrics.append(entry)
assert len(metrics)==14
c=Client();project=c.identity()
errors=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
state=c.resource('mcpforunity://editor/state');p=probe(c);idle(p)
checkpoint=D/('preinstall_checkpoint_20261029'+tag+'.json')
write(checkpoint,{'recorded_at':now(),'art_revision':'art_r01','layout_revision':'layout_r02','selected':read(D/'art_selection.json'),'project':project,'errors':errors,'state':state,'probe':p,'pixel_metrics':metrics,'staged_files':{f.relative_to(D).as_posix():sha(f) for f in art.iterdir() if f.is_file()},'protocol_history':c.history},True)
stage('art_r01_staged_reviewed_ready_to_install',checkpoint)
print(json.dumps({'project':project,'probe':p,'metrics':metrics,'scope_pass':True},ensure_ascii=False))
