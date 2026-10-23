"""L02 authored decisions; every gameplay value below is a literal decision."""
from formal_tools import *
gold_ids=[2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30]
spec={'records':{f'SceneInfo:{i}':{'initialGold':{'value':100,'reason':'用户硬约束：基础金币固定100；各关另行重做开局与收入'}} for i in gold_ids},'waves':[]}
# wave, gap, clear, explicit named enemy edits, tactical decision
rows=[
(1,300,24,{'Chick':{'hp':8.5,'speed':1.10},'Chicken':{'hp':8.5,'speed':1.10}},'三普开局，先付96；32只双种小怪检验近出生点覆盖'),
(2,290,28,{'Chick':{'hp':9.5,'speed':1.10},'Chicken':{'hp':9.5,'speed':1.10}},'首次补建和90升级二选一，保留普通塔两击阈值'),
(3,260,30,{'Chick':{'hp':12},'Chicken':{'hp':12},'Larva':{'hp':7}},'密集幼虫给首座爆破塔有效群攻机会'),
(4,300,36,{'Chick':{'hp':13.5},'Chicken':{'hp':13.5},'Larva':{'hp':9}},'恢复投资窗，为W5两线火力预留资金'),
(5,250,34,{'@air':{'hp':13,'speed':1.08}},'首次空袭，正中走廊普通塔需兼顾空地'),
(6,310,30,{'@air':{'hp':12,'speed':1.04}},'低压清理，允许补减速而非连续加伤害'),
(7,220,36,{'@air':{'hp':16,'speed':1.12}},'第一次密集地空抢火，爆破负责地面'),
(8,255,32,{'@air':{'hp':16,'speed':1.06}},'给折返墙施工一波，避免只升级单塔'),
(9,260,38,{'@air':{'hp':18,'speed':1.10}},'投资窗末尾检查中段对空覆盖'),
(10,215,40,{'@air':{'hp':32,'speed':1.12}},'第一考核波，防空两次命中阈值跃迁'),
(11,260,36,{'@air':{'hp':27,'speed':1.08}},'快地面和重甲入场，群攻分流才不争抢普通塔'),
(12,300,30,{'@air':{'hp':26,'speed':1.05}},'收入偏小但时间宽的升级恢复段'),
(13,230,42,{'@air':{'hp':31,'speed':1.10}},'第二轮空地抢火，提高减速覆盖价值'),
(14,240,36,{'@air':{'hp':35,'speed':1.14}},'密度稍缓，W15前最后的资金调整'),
(15,195,44,{'@air':{'hp':56,'speed':1.13}},'中盘峰值，防空升级与地面爆破必须分工'),
(16,280,32,{'@air':{'hp':50,'speed':1.08}},'回血压恢复窗；不返还生命，只降低出生密度'),
(17,250,38,{'@air':{'hp':53,'speed':1.12}},'重新施压但非机械递增HP'),
(18,210,42,{'@air':{'hp':57,'speed':1.12}},'长地面队列考核重复覆盖和爆破'),
(19,230,36,{'@air':{'hp':61,'speed':1.16}},'提高空中穿越速度，终点补漏塔收益上升'),
(20,185,48,{'@air':{'hp':98,'speed':1.15}},'末段重压，三级普通塔主对空'),
(21,260,34,{'@air':{'hp':90,'speed':1.08}},'第二恢复段，允许二级减速向三级投资'),
(22,240,38,{'@air':{'hp':94,'speed':1.12}},'保留中等持续压，控制收入不与旧等级同比膨胀'),
(23,220,42,{'@air':{'hp':96,'speed':1.18}},'加速空袭检验末端覆盖'),
(24,300,46,{'@air':{'hp':92,'speed':1.10}},'终局准备窗，末波奖励不可预支'),
(25,155,52,{'@air':{'hp':168,'speed':1.12}},'终局合流，保留独立重型精英而非虚构Boss能力')]
for wave,gap,clear,enemies,reason in rows:spec['waves'].append(dict(level=2,wave=wave,gap=gap,clear=clear,enemies=enemies,reason=reason))
(REPORT/'design-L02-r1.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
manifest(REPORT/'design-L02-r1.json')
