# v6 实验配方生成器：从正式配方派生 A/B 两组候选，供离线仿真对比，不写入正式配方。
# 用法: python make_recipes.py
import copy, json, pathlib

HERE = pathlib.Path(__file__).parent
SRC = HERE.parents[2] / 'Luban/BalanceDesign/balance_design.json'

base = json.loads(SRC.read_text(encoding='utf-8'))

# ── 方案 A：严格按 Prompt 第 3 节建议值（用于验证其全局副作用）──────────────
A = copy.deepcopy(base)
A['balanceRevision'] = 'balance-30x25-tight-v6-expA'
A['formula'].update({
    'initialGold': 200, 'rewardBase': 26,
    'countOffset': 8, 'countLevelCoefficient': 3, 'countWaveCoefficient': 6,
    'minSpawnMs': 200, 'baseEhpPerUnit': 24,
    'waveLinear': 0.12, 'waveQuadratic': 0.028,
    'levelEhpGrowth': 0.07, 'minBudgetGrowth': 1.05, 'finalMultiplier': 1.25,
})
A['roles']['air']['weight'] = 1.05
# unlockSchedule air W3/W5 会被管线 L1 W7 守卫拒绝，实验 A 保持 W7/W8/W10 不动。

# ── 方案 B：数量参数全调 + L1 专属 override 增压，全局 EHP 公式保持 v5 ──────
B = copy.deepcopy(base)
B['balanceRevision'] = 'balance-30x25-tight-v6-expB'
B['formula'].update({
    'initialGold': 200, 'rewardBase': 26,
    'countOffset': 11, 'countLevelCoefficient': 3, 'countWaveCoefficient': 6,
    'minSpawnMs': 200, 'minBudgetGrowth': 1.03, 'finalMultiplier': 1.20,
    # baseEhpPerUnit/waveLinear/waveQuadratic/levelEhpGrowth 保持 v5，保护 30 关可通关
})
B['roles']['air']['weight'] = 1.0
# L1 血量 ×2.35 全部走 L1 专属 tighten（1.191×2.35≈2.7989），不碰全局公式
for o in B['overrides']:
    if o['id'] == 'L1-tighten':
        o['value'] = 2.7989

(HERE / 'recipeA.json').write_text(json.dumps(A, ensure_ascii=False, indent=2), encoding='utf-8')
(HERE / 'recipeB.json').write_text(json.dumps(B, ensure_ascii=False, indent=2), encoding='utf-8')
print('written recipeA.json / recipeB.json')
