"""Individually authored literal decisions for L03-L06; not a scaling formula.

Each line is a reviewed wave: gap(ms), clear gold, air HP, air speed.
Unlisted enemy fields, compositions and IDs retain the audited source values.
"""
from formal_tools import *
DATA={
3:('中央8格空路，分段防空', '''340 24 0 0
300 28 0 0
280 32 0 0
320 38 0 0
330 32 10.5 1.05
300 34 12 1.10
280 38 14 1.12
200 44 18 1.25
320 32 16 1.08
240 40 24 1.12
300 36 23 1.10
340 30 21 1.05
280 40 28 1.16
190 48 35 1.28
300 38 38 1.14
260 34 40 1.12
220 44 46 1.20
300 34 43 1.08
260 40 52 1.16
180 50 70 1.28
310 32 62 1.08
230 42 68 1.20
280 38 72 1.16
340 44 66 1.10
180 54 84 1.22''',
{1:{'Chick':{'hp':8.5,'speed':1.10,'reward':2},'Chicken':{'hp':8.5,'speed':1.10,'reward':2}},2:{'Chick':{'hp':9.5,'speed':1.12},'Chicken':{'hp':9.5,'speed':1.12}},3:{'Chick':{'hp':12},'Chicken':{'hp':12},'Larva':{'hp':7.5}},4:{'Chick':{'hp':14},'Chicken':{'hp':14},'Larva':{'hp':9}}},
{8:'短空路第一峰值，检验缓速覆盖而非地面路线长度',14:'快空袭抢占普通塔，留爆破处理地面',20:'高频短空路专考，不让地面减速代替防空',24:'末波资金准备，降低密度但不能预支清波奖励'}),
4:('反向15格空路，前压与终点留金', '''310 22 0 0
290 30 0 0
250 34 0 0
330 40 0 0
280 34 14 1.08
310 32 13 1.05
200 44 18 1.18
270 34 17 1.08
240 38 22 1.14
320 32 29 1.08
250 42 29 1.12
280 36 31 1.10
190 48 38 1.22
260 36 36 1.10
210 46 61 1.16
330 32 52 1.08
250 40 56 1.12
230 44 60 1.16
180 50 68 1.26
230 44 101 1.18
300 34 94 1.10
260 40 96 1.16
220 46 104 1.22
340 48 98 1.08
165 56 176 1.20''',
{1:{'Chick':{'hp':9,'speed':1.10,'reward':2},'Chicken':{'hp':9,'speed':1.10,'reward':2}},2:{'Chick':{'hp':10,'speed':1.12,'reward':2},'Chicken':{'hp':10,'speed':1.12,'reward':2}},3:{'Chick':{'hp':12.5},'Chicken':{'hp':12.5},'Larva':{'hp':8}},4:{'Chick':{'hp':15},'Chicken':{'hp':15},'Larva':{'hp':10}},7:{'Chick':{'speed':1.35},'Chicken':{'speed':1.35}},13:{'LittleBunny':{'speed':1.85}},19:{'LittleBunny':{'speed':1.95}}},
{7:'地面提速并密集出场，出生端普通塔与爆破取舍',13:'快地面与空中同时提速，考核两线资金',19:'末段前压，终点不可全占为低价值墙',24:'留出最后一轮末端补建与升级时间'}),
5:('向上8格短空路，低级覆盖转升级', '''350 24 0 0
310 30 0 0
270 36 0 0
340 42 0 0
340 34 11 1.05
290 36 13 1.12
240 42 16 1.18
300 34 15 1.08
185 48 22 1.30
280 38 26 1.14
250 42 29 1.18
330 32 25 1.08
260 40 32 1.20
280 36 34 1.16
180 52 44 1.32
310 34 40 1.10
230 46 48 1.24
280 38 46 1.14
220 46 55 1.26
250 44 65 1.18
320 34 59 1.10
175 54 75 1.34
280 40 71 1.18
350 46 68 1.12
185 58 94 1.28''',
{1:{'Chick':{'hp':8,'speed':1.10,'reward':2},'Chicken':{'hp':8,'speed':1.10,'reward':2}},2:{'Chick':{'hp':10,'speed':1.10,'reward':2},'Chicken':{'hp':10,'speed':1.10,'reward':2}},3:{'Chick':{'hp':13},'Chicken':{'hp':13},'Larva':{'hp':7}},4:{'Chick':{'hp':15.5},'Chicken':{'hp':15.5},'Larva':{'hp':9.5}},9:{'Chick':{'speed':1.30}},15:{'Scarab':{'speed':0.95}},22:{'LittleBunny':{'speed':2.05}}},
{9:'短空路第一轮快袭，避免普通塔全部锁地面',15:'中期双线峰值，重甲提速但不增加虚构能力',22:'空中最高速度窗，三级缓速与普通塔升级择时',24:'终局投资窗，保持末波必要施工余量'}),
6:('对角17格空路，绕障碍两翼分工', '''300 24 0 0
280 30 0 0
250 36 0 0
320 42 0 0
270 36 15 1.10
210 46 18 1.22
250 40 20 1.16
330 32 18 1.08
260 42 24 1.18
230 46 34 1.20
190 52 36 1.26
280 38 32 1.12
250 44 38 1.18
260 40 42 1.16
200 52 68 1.22
340 34 58 1.08
250 44 62 1.18
175 56 70 1.30
270 40 67 1.14
210 54 112 1.22
300 36 100 1.10
240 48 106 1.20
330 38 104 1.12
280 48 118 1.20
155 60 204 1.26''',
{1:{'Chick':{'hp':9,'speed':1.10,'reward':2},'Chicken':{'hp':9,'speed':1.10,'reward':2}},2:{'Chick':{'hp':10.5,'speed':1.12,'reward':2},'Chicken':{'hp':10.5,'speed':1.12,'reward':2}},3:{'Chick':{'hp':13.5},'Chicken':{'hp':13.5},'Larva':{'hp':8}},4:{'Chick':{'hp':16},'Chicken':{'hp':16},'Larva':{'hp':10}},6:{'Chick':{'speed':1.35}},11:{'LittleBunny':{'speed':1.90}},18:{'Scarab':{'speed':0.98}}},
{6:'早期两翼压力，选购防空还是补爆破',11:'绕障碍快怪，地面与斜线覆盖分账',18:'重甲提速压缩地面多次覆盖窗口',25:'终局斜线合流，不能依靠无限出售延时'})}
spec={'records':{},'waves':[]}
for level,(theme,raw,ground,windows) in DATA.items():
    rows=[line.split() for line in raw.splitlines() if line.strip()];assert len(rows)==25
    for wave,(gap,clear,airhp,airspeed) in enumerate(rows,1):
        enemies=ground.get(wave,{}).copy()
        if float(airhp)>0:enemies['@air']={'hp':float(airhp),'speed':float(airspeed)}
        reason=theme+'；'+windows.get(wave,'独立安排本波密度与清波资金；其余怪物属性、准确数量及顺序沿用本波审计记录')
        spec['waves'].append(dict(level=level,wave=wave,gap=int(gap),clear=int(clear),enemies=enemies,reason=reason))
path=REPORT/'design-L03-L06-r1.json';path.write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8');manifest(path)
