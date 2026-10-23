"""Explicitly selected per-wave literals after real r1 failure analysis; no scaling."""
from formal_tools import *
import openpyxl

# Each tuple is a separate design decision: wave, air HP, air speed, spawn gap.
# Unlisted waves, rewards, counts, order, ground variants and maps stay frozen.
DATA={
8:('斜线交接末波：长路线方案地面可撑至81秒，但空袭漏11只，单次覆盖断档；保留群怪血量，以较慢空速给中后段普通塔第二次接力',[(25,172,1.22,210)]),
9:('反向斜线末波：长路线空中累计12漏，地面短线方案末波则抢不到火力；降低末波单体空中击杀阈值，保留反向部署与地空抢火考核',[(25,168,1.22,215)]),
10:('双走廊：W20地面小额残血漏怪与W25早期地面穿越同时出现，普通塔被空袭牵制；分别留出两次击杀转火窗口，尚不降低地面变体',[(20,112,1.20,260),(25,186,1.24,210)]),
14:('障碍通道复用：长路线W12仅1HP空中漏怪、W20仅1.9HP地面漏怪，W25空中大幅过载；中期只留少量接力余量，终局降低空中连续占火时间',[(12,70,1.34,185),(25,205,1.30,205)]),
15:('第一次综合考核：长路线W15/20空袭已累计11漏，现有中期投资来不及同时承受高血量与高密度；保留五次峰值，分别修正三次过载而不改恢复波',[(15,94,1.34,220),(20,154,1.34,210),(25,232,1.34,195)]),
16:('从铺场到升级：原长路线前24波无漏，终局空袭338HP超过已有升级覆盖；保持前24波考核，末波转为240HP的更长接力队列',[(25,240,1.32,210)]),
18:('反向终点预留：长路线W15空袭即失守，短路线到W22地面失守；两者都存在普通塔长期占空的问题，修正两次峰值和终局接力，保留群攻需求',[(15,94,1.34,210),(22,180,1.38,200),(25,242,1.36,205)]),
19:('对角跨区：W16单只空中大残血、W23十只空中穿越；将两段快袭改为仍快于恢复段但可分区接力的阈值，终局保留46只空中压迫',[(16,126,1.36,200),(23,192,1.38,205),(25,262,1.38,210)]),
20:('压缩冗余：长路线W11与W18已累计10次空中漏怪，W25高血量空袭无补救空间；保留短间隔峰值的相对关系，分别拉开三次施工后的检验窗口',[(11,66,1.34,205),(18,134,1.36,205),(25,270,1.38,210)]),
21:('靠边斜线塔位稀缺：长路线W21空袭直接失守，空路服务位少于居中地图；采用较低单体阈值与较长队列保留高等级核心的价值',[(14,96,1.34,205),(21,166,1.40,200),(25,262,1.36,220)]),
22:('下侧反向斜线：W15已漏3只空中，W22再漏9只；让上一恢复窗的防空投资有可见收益，保留终局48只空中的资金分配要求',[(15,120,1.36,210),(22,186,1.40,205),(25,272,1.40,215)]),
23:('重型队列错峰：W16空中累计11漏遮蔽地面AOE作用，W23仍有突发空中缺口；缩短单体占火并延长相邻出生，保留大体量重型队列',[(16,146,1.38,210),(23,222,1.42,215),(25,292,1.40,220)]),
24:('恢复窗有限：长路线前24波满血，末波462HP空袭直接失守；仅修正终局阈值和间隔，避免破坏已成立的中期压力与升级链',[(25,292,1.40,210)]),
25:('终局资金预留：短路线在W20地面失守且长路线开局需另寻塔位；本次先修正最强的三次空袭，不把代理开局失败当作数据无解，也不降低开局或地面血量',[(14,130,1.38,210),(20,212,1.32,300),(21,242,1.40,205),(25,332,1.44,220)]),
27:('上斜线转换：长路线W15空中失守、短路线W22空中失守；先使两次不同覆盖段的防空投入均能发挥作用，保留最后阶段多区资金分配',[(15,126,1.36,215),(22,206,1.42,210),(25,316,1.42,220)]),
28:('既有22步地路：多类布局在W16空中首次明显失守，后续W23再遭空中叠压；利用既有地路保留地面强度，重定两次空袭与终局的接力时间',[(16,172,1.40,215),(23,262,1.44,220),(25,332,1.44,225)]),
29:('中下斜线：短路线W20地面残血，W21空中与地面同时漏；降低空袭占用普通塔的连续时间，保留高等级塔与低级铺场的投资取舍',[(14,112,1.38,220),(20,222,1.34,320),(21,232,1.40,215),(25,342,1.42,230)]),
30:('综合配资：短路线W15地面失守，长路线同波空中漏9只、W20继续失守；分开单体血量、速度和密度的极端叠加，保留五段峰值和最后48只空袭',[(15,142,1.40,225),(20,242,1.46,220),(25,352,1.46,225)])}

waves=json.loads((REPORT/'audit/formal-waves-r1.json').read_text(encoding='utf-8'));spec={'status':'reviewed_literal_decisions_pending_apply','waves':[]};edits=[];books={}
def add(record,field,value,reason):
 p=record['path'];cell=record['cells'][field]
 if p not in books:books[p]=openpyxl.load_workbook(ROOT/p,read_only=True)
 before=books[p][record['sheet']][cell].value
 if before!=value:edits.append(dict(path=p,sheet=record['sheet'],cell=cell,before=before,after=value,reason=reason))
for level,(reason,rows)in DATA.items():
 for wave,hp,speed,gap in rows:
  w=next(w for w in waves if w['level']==level and w['wave']==wave)
  spec['waves'].append(dict(level=level,wave=wave,gap=gap,enemies={'@air':{'hp':hp,'speed':speed}},reason=reason))
  add(w['sourceGroups'][0],'enemyInterval',gap,reason)
  for v in w['variants']:
   if v['data']['isFlying']:
    add(v['source'],'hp',hp,reason);add(v['source'],'speed',speed,reason)
for wb in books.values():wb.close()
(REPORT/'design-air-refinement-r2.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
(REPORT/'design-air-refinement-r2.cells.json').write_text(json.dumps(edits,ensure_ascii=False,indent=2),encoding='utf-8')
print(len(DATA),'levels',len(spec['waves']),'independent wave refinements',len(edits),'literal cells; not applied')
