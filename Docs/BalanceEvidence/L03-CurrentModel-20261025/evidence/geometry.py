from candidates import *
from balance_maze import search as maze_search
trials=[]
for seed in [73,1073,2073,3073]:
    r=maze_search(cells,seed,iterations=1000)
    trials.append(r)
dump(OUT/'geometric-layout-search.json',{'trials':trials,'evaluatedLayouts':sum(t['evaluatedLayouts'] for t in trials),'purpose':'Geometric route candidates only; not gameplay wins or star certification'})
for t in trials:print(t['seed'],t['evaluatedLayouts'],t['pathLength'],t['towerCount'])
