from focused import *
def build_plan(seed,aw,gb,slowboost):
    rng=random.Random(seed);ops=[];built={};spent=0;extraspent=0
    base=[dict(o) for o in old if o['action']=='build']
    walls={(o['col'],o['row']) for o in base}
    # All original maze walls retained; avoid idle outer tangent towers.
    extra=[]
    for x in [9,8,7,6,10]:
        for y in range(9):
            c=(x,y)
            if c in walls or cells[y][x]!='.' or aircov(c,2.3)<.4:continue
            if path_for(cells,walls|set(extra)|{c}):extra.append(c)
    for wave in range(1,26):
        gold=income_boundary(wave)-spent
        for o in base:
            if o['waveOrdinal']!=wave:continue
            c=(o['col'],o['row']);tid=o['towerId'];cost=table[tid]['prices'];built[c]=tid;spent+=cost;gold-=cost;ops.append(dict(o))
        if wave<=5:continue
        reserve=min(income_boundary(w)-sum(table[o['towerId']]['prices'] for o in base if o['waveOrdinal']<=w) for w in range(wave,26))-extraspent
        gold=min(gold,reserve)
        for k in range(200):
            path=path_for(cells,built);options=[]
            for c,t in built.items():
                nxt=table[t]['upgradeTo']
                if not nxt or table[nxt]['prices']>gold:continue
                a=aircov(c,table[nxt]['radius']);g=cov(c,path,table[nxt]['radius'])
                # Upgrade early-entry area towers, not idle towers at corridor end.
                front=1 if c[1]<=4 else .6
                if table[t]['type']==3:gain=(table[nxt]['effectValue']-table[t]['effectValue'])*(a*aw*slowboost+g)*100
                else:gain=(table[nxt]['power']*1000/table[nxt]['CD']-table[t]['power']*1000/table[t]['CD'])*(a*aw+g*(gb*front if table[t]['type']==2 else .1))
                gain/=table[nxt]['prices'];gain*=rng.uniform(.9,1.1)
                options.append((gain,c,nxt,'upgrade'))
            for c in extra:
                if c in built:continue
                p=path_for(cells,list(built)+[c])
                if not p:continue
                tid=1;a=aircov(c,2);g=cov(c,p,2)
                if table[tid]['prices']>gold or a<.5:continue
                gain=(13.3333*(a*aw+g*.1)+max(0,len(p)-len(path))*5)/32
                options.append((gain*rng.uniform(.9,1.1),c,tid,'build'))
            if not options:break
            _,c,tid,act=max(options);cost=table[tid]['prices'];built[c]=tid;gold-=cost;spent+=cost;extraspent+=cost
            ops.append({'waveOrdinal':wave,'timeMs':0,'action':act,'row':c[1],'col':c[0],'towerId':tid})
    return ops
if __name__=='__main__':
    paths=[]
    for i,(aw,gb,sb) in enumerate([(5,2,3),(10,3,3),(20,4,3),(10,5,4),(20,6,4),(30,6,4),(10,10,5),(30,10,5)]):
        p=OUT/'candidates'/('fixed-'+str(i)+'.json');dump(p,build_plan(380+i,aw,gb,sb));paths.append(p)
    print(request('fixed-batch',paths,True,step=.05))
