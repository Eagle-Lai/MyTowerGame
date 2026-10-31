from candidates import *
def aircov(cell,radius):
    return sum((cell[0]-8)**2+(cell[1]-i/10)**2<radius*radius for i in range(81))/10
def focused(seed,aw,slowboost,groundboost):
    rng=random.Random(seed);built={};ops=[];spent=0
    seedBuilds=[o for o in old if o['action']=='build'];walls={(o['col'],o['row']) for o in seedBuilds}
    extras=[]
    for x in [9,8,7,10,6]:
        for y in range(9):
            c=(x,y)
            if c in walls or cells[y][x]!='.' or aircov(c,2)<.5:continue
            if path_for(cells,walls|set(extras)|{c}):extras.append(c)
    final=path_for(cells,walls|set(extras))
    for wave in range(1,26):
        gold=income_boundary(wave)-spent
        if wave<=5:
            for o in old:
                if o['waveOrdinal']!=wave:continue
                c=(o['col'],o['row']);tid=o['towerId'];built[c]=tid;spent+=table[tid]['prices'];ops.append(dict(o))
            continue
        for k in range(200):
            options=[];path=path_for(cells,built)
            for c,t in built.items():
                nxt=table[t]['upgradeTo']
                if not nxt or table[nxt]['prices']>gold:continue
                a=aircov(c,table[nxt]['radius']);g=cov(c,path,table[nxt]['radius'])
                if table[t]['type']==3:
                    score=(table[nxt]['effectValue']-table[t]['effectValue'])*(a*aw*slowboost+g*.7)*100
                else:
                    score=(table[nxt]['power']*1000/table[nxt]['CD']-table[t]['power']*1000/table[t]['CD'])*(a*aw+g*(groundboost if table[t]['type']==2 else .15))
                options.append((score/table[nxt]['prices']*rng.uniform(.9,1.1),c,nxt,'upgrade'))
            for c in list(walls)+extras:
                if c in built:continue
                pp=path_for(cells,list(built)+[c])
                if not pp:continue
                o=next((o for o in seedBuilds if (o['col'],o['row'])==c),None)
                tid=o['towerId'] if o else 1
                if table[tid]['prices']>gold:continue
                a=aircov(c,2);g=cov(c,pp,2)
                gain=len(pp)-len(path)
                score=(13.33*(a*aw+g*.3) if tid==1 else 16*g*groundboost if tid==4 else (a*aw*slowboost+g)*15)
                score+=gain*10+cov(c,final,2)*2
                options.append((score/table[tid]['prices']*rng.uniform(.9,1.1),c,tid,'build'))
            if not options:break
            _,c,tid,act=max(options);cost=table[tid]['prices'];gold-=cost;spent+=cost;built[c]=tid
            ops.append({'waveOrdinal':wave,'timeMs':0,'action':act,'row':c[1],'col':c[0],'towerId':tid})
    return ops
if __name__=='__main__':
    paths=[]
    for i,(aw,sb,gb) in enumerate([(8,3,1),(20,3,1),(40,3,1),(20,8,1),(20,3,3),(40,8,2)]):
        p=OUT/'candidates'/('focused-'+str(i)+'.json');dump(p,focused(250+i,aw,sb,gb));paths.append(p)
    print(request('focused-batch',paths,True,step=.05))
