"""Rebuild the per-level EHP overrides so every level is equally tight (EHP per capacity)."""
import sys, json, pathlib
sys.path.insert(0, 'D:/FreedomTower_1/.workbuddy/tools')
import balance_pipeline as bp, balance_fill_gate as g
from balance_campaign import capacity

TARGET = float(sys.argv[1]) if len(sys.argv) > 1 else 2050.0
SOURCE_RECIPE = 'Luban/BalanceDesign/FillGate/rounds/round-13/recipe.json'
base = bp.read_json(SOURCE_RECIPE)
plan = bp.generate(base, 'D04')
caps = {L: capacity(g.level_map(plan, L)['cells'])['capacity'] for L in range(1, 31)}
cur = {L: sum(x['actualEhp'] for x in plan['waves'] if x['levelId'] == L) for L in range(1, 31)}
target, prev = {}, 0.0
for L in range(1, 31):
    want = max(TARGET * caps[L], prev * 1.005)
    target[L] = want
    prev = want
recipe = json.loads(json.dumps(base))
recipe['balanceRevision'] = 'balance-30x25-tight-v5'
for attempt in range(30):
    recipe['overrides'] = []
    for L in range(1, 31):
        m = round(max(0.6, min(3.6, target[L] / cur[L])), 4)
        recipe['overrides'].append({'id': f'L{L}-tighten', 'target': 'wave', 'scope': 'level',
                                    'levelId': L, 'field': 'targetEhp', 'mode': 'multiply', 'value': m})
    plan2 = bp.generate(recipe, 'D04')
    errors = bp.validate(plan2)['errors']
    if not errors:
        break
    # Strict monotonicity: nudge the offending level up and retry.
    bumped = set()
    for e in errors:
        if 'EHP not strictly increasing L' in e:
            bumped.add(int(e.split('L')[1].split()[0]))
    if not bumped:
        raise SystemExit('non-EHP validation errors: ' + '; '.join(errors[:3]))
    for L in bumped:
        target[L] *= 1.01
pathlib.Path('Luban/BalanceDesign/FillGate/rounds/round-18/recipe.json').write_text(
    json.dumps(recipe, ensure_ascii=False, indent=2), encoding='utf-8')
pathlib.Path('Luban/BalanceDesign/balance_design.json').write_text(
    json.dumps(recipe, ensure_ascii=False, indent=2), encoding='utf-8')
per = [round(sum(x['actualEhp'] for x in plan2['waves'] if x['levelId'] == L) / caps[L]) for L in range(1, 31)]
print(json.dumps({'target': TARGET, 'attempt': attempt + 1, 'perC': per}))
