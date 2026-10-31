from candidates import *
DOC=ROOT/'Docs/BalanceEvidence/L03-CurrentModel-20261025'
DOC.mkdir(parents=True,exist_ok=True)
rating=next(r for r in plan['tables']['tblevelrating'] if r['id']==3)
lower=sum((w['count']-1)*w['spawnIntervalMs'] for w in plan['waves'])
dump(DOC/'rating-time-feasibility.json',{'levelId':3,'runtimeContentHash':rating['runtimeContentHash'],'planHash':rating['planHash'],'enemyCount':sum(w['count'] for w in plan['waves']),'fiveStarLimitMs':rating['parCombatTimeMs'],'fourStarLimitMs':rating['parCombatTimeMs']*rating['fourStarTimePermille']//1000,'lastSpawnTimeSumMs':lower,'strictConservativeLowerBoundMsAt20ms':lower-25*20,'fiveStarsReachableUnderCurrentPacing':False,'reason':'Each wave must finish spawning before the next wave; sum of last scheduled spawn times already exceeds both star time limits. This excludes travel and killing time.','waveBounds':[{'wave':w['waveOrdinal'],'enemies':w['count'],'gapMs':w['spawnIntervalMs'],'lastSpawnMs':(w['count']-1)*w['spawnIntervalMs']} for w in plan['waves']]})
dump(DOC/'input-hashes.json',json.loads((OUT/'input-hashes.json').read_text()))
text='''# 第3关：当前数值模型的阵型搜索与通关记录

## 已确认的五星时间冲突

当前正式配置为5082只怪、25波、初始100金币和12生命；击杀奖励按80%累计结算。

按每波敌人数和出怪间隔计算，仅等待每波最后一只怪出生，合计就需1345.28秒。即使保守扣除每波一帧20毫秒，仍至少1344.78秒，超过五星870秒和四星1000.5秒限时。正常流程不能提前开启尚未完成的波次，倍速也不缩短评级使用的战斗时间。因此当前模型的合法五星在时间条件上不可达；满血零漏怪实际最多评为三星。

依据：Assets/Scripts/Round/WaveManager.cs的BeginRound/Tick/IsRoundFinished；Assets/Scripts/Data/LevelRating.cs的唯一评级入口。逐波下界与输入指纹见同目录JSON。

本轮只搜索操作方案，不改关卡数值、出怪时间轴、金币规则或评级门槛。最终阵型与操作将在真实Unity回放后补齐。
'''
(DOC/'完整操作与测试报告.md').write_text(text,encoding='utf-8-sig')
print(DOC)
