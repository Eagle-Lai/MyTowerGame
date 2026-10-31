from candidates import *
paths=[]
for idx in [1,2]:
    p=OUT/'candidates'/('fixed-'+str(idx)+'.json');paths.append(p)
p=request('precise-zero',paths,True,step=.02)
# This queued request has not run yet; replace with already-found zero-leak verification.
queued=OUT/'reactive-batch.request.json';shutil=None
queued.write_text(p.read_text(),encoding='utf-8')
print(p)
