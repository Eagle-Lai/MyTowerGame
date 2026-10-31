from candidates import *
def snake(seed,spacing=2,flip=0,aw=5):
    rng=random.Random(seed)
    walls=[]
    for i,y in enumerate(range(2,8,spacing)):
        opening=16 if (i+flip)%2==0 else 0
        walls.extend((x,y) for x in range(17) if x!=opening)
    initial=[(8,6),(8,4),(8,2)] if spacing==2 else [(8,6),(8,5),(8,2)]
    for cell in initial:
        if cell not in walls:walls.insert(0,cell)
    final=path_for(cells,walls)
    if not final:return None
    built={};ops=[];spent=0;slowtargets=[(8,2),(8,6)]
    for wave in range(1,26):
        gold=income_boundary(wave)-spent
        for k in range(200):
            path=path_for(cells,built);options=[]
            for c,t in built.items():
                nxt=table[t]['upgradeTo']
                if not nxt or table[nxt]['prices']>gold or wave<9:continue
                a=sum((c[0]-8)**2+(c[1]-yy)**2<=table[nxt]['radius']**2 for yy in range(9))
                g=cov(c,path,table[nxt]['radius'])
                if table[t]['type']==3:gain=(table[nxt]['effectValue']-table[t]['effectValue'])*200*(a*aw+g)
                else:gain=(table[nxt]['power']*1000/table[nxt]['CD']-table[t]['power']*1000/table[t]['CD'])*(a*aw+g*(3 if table[t]['type']==2 else .2))
                options.append((gain/table[nxt]['prices']*rng.uniform(.85,1.15),c,nxt,'upgrade'))
            for cell in walls:
                if cell in built:continue
                p=path_for(cells,list(built)+[cell])
                if not p:continue
                air=sum((cell[0]-8)**2+(cell[1]-y)**2<=4 for y in range(9))
                nearair=abs(cell[0]-8)<=1
                tid=7 if cell in slowtargets and wave>=2 else 1 if nearair else 4 if (cell[0]+seed)%3==0 else 1
                if table[tid]['prices']>gold:continue
                score=(len(p)-len(path))*1.5+cov(cell,p,2)*.6+cov(cell,final,2)*.4+air*aw
                # Finish connected walls so every late tower can see the corridor.
                score+=sum(abs(cell[0]-c[0])+abs(cell[1]-c[1])==1 for c in built)*1.5
                score*=rng.uniform(.8,1.2)
                options.append((score*13.33/table[tid]['prices'],cell,tid,'build'))
            # Service towers off the final path defend the fixed air route.
            for y in range(9):
                for x in range(7,10):
                    cell=(x,y)
                    if cell in built or cell in final or cell in walls or cells[y][x]!='.':continue
                    p=path_for(cells,list(built)+[cell])
                    if not p:continue
                    tid=1
                    if table[tid]['prices']>gold:continue
                    air=sum((x-8)**2+(y-yy)**2<=4 for yy in range(9))
                    options.append(((air*aw+cov(cell,p,2)*.3)*13.33/32*rng.uniform(.8,1.2),cell,tid,'build'))
            if wave==1:
                cell=next((c for c in initial if c not in built),None)
                if cell is None:break
                best=(0,cell,1,'build')
            elif options:best=max(options)
            else:break
            _,cell,tid,action=best;cost=table[tid]['prices']
            if cost>gold:break
            built[cell]=tid;gold-=cost;spent+=cost
            ops.append({'waveOrdinal':wave,'timeMs':0,'action':action,'row':cell[1],'col':cell[0],'towerId':tid})
    return ops
if __name__=='__main__':
    paths=[];metadata=[]
    for i,(sp,flip,aw) in enumerate([(2,0,4),(2,1,4),(3,0,5),(3,1,5),(2,0,10),(2,1,10),(3,0,15),(3,1,15)]):
        ops=snake(100+i,sp,flip,aw)
        if not ops:continue
        p=OUT/'candidates'/('snake-v2-'+str(i)+'.json');dump(p,ops);paths.append(p)
        metadata.append({'path':str(p),'spacing':sp,'flip':flip,'airWeight':aw,'operations':len(ops)})
    dump(OUT/'snake-candidates.json',metadata)
    print(request('snake-batch-v2',paths,True,step=.05))
