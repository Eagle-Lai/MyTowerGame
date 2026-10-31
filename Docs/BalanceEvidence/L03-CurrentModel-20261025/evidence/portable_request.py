from finalize import *
ops=DOC/'best-operations.json'
req={'output':'D:/FreedomTower_1/Library/L03SavedStrategyReplay','stepSeconds':.02,'stepsPerUpdate':100,'batchTimeoutSeconds':1800,'keepPlaying':True,'captureOutcomes':True,'runs':[{'profileId':'D04','levelId':3,'strategy':'replay','speed':1,'operationsPath':str(ops).replace(chr(92),'/'),'waitForFunds':False,'captureStages':True,'screenshots':True,'wallTimeoutSeconds':300}]}
dump(DOC/'replay-request.json',req)
print('Saved durable one-run reproduction request')
