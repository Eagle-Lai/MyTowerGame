from finalize import *
doc=DOC/'完整操作与测试报告.md'
text=doc.read_text(encoding='utf-8-sig')
rp=DOC/'reproducibility.json'
if rp.exists():
    repro=json.loads(rp.read_text());text+='''
## 严格复跑与操作容错

|记录|严格时间|有效|击杀|漏怪|生命|星级|战斗秒|同初次关键数据一致|
|---|---|---|---:|---:|---:|---:|---:|---|
'''
    for x in repro['runs']:
        name='严格复跑'+str(x['index']+1) if x['exactTimingReplay'] else '全部波内操作延后0.5秒'
        text+=f"|{name}|{x['exactTimingReplay']}|{x['valid']}|{x['killed']}|{x['leaked']}|{x['hp']}/12|{x['stars']}|{x['combatSeconds']:.2f}|{x['equalToSelected']}|\n"
    text+='\n严格复跑没有等待资金兜底：每笔操作到达时刻必须已有足够整数金币；失败则立即拒绝。浮点数对比容差0.00001，排除runId、spawnSerial等身份与观测元数据。\n'
text+='''
## 观测与验证限制

这是Unity真实场景和游戏系统的固定步长回放，非外部简化模拟器。正常的放置、升级、寻路、自动开波、击杀金币和唯一评级入口均参与运行。它不是逐次鼠标拖拽录像；操作表用于玩家照做，P暂停是已有正常功能。

为减少搜索耗时，后期关闭了仅编辑器使用的“离开射程后重新进入”观测计数；没有改伤害、目标选择、速度、资金、时钟和出怪。不能把后期repeatEffectEnemies=0解释为没有重复覆盖。实际伤害、对空命中、金币、结算和路径仍完整记录。

本轮未修改C#、配置源表或导出JSON；指纹核对见unchanged-input-verification.json。编辑器历史Unity Remote环境检查异常单独保留；没有清空控制台。
'''
doc.write_text(text,encoding='utf-8-sig')
print('final notes appended')
