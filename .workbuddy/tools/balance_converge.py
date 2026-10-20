"""Convergence helpers for the FreedomTower fill-gate campaign.

`report` prints the gate matrix as a compact table so each round can be read at a
glance. `adjust` applies per-level multipliers to the `targetEhp` overrides, then
repairs the cross-level strict-increase contract that `validate()` enforces.
"""
import argparse, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import balance_pipeline as bp

DEFAULT_RECIPE = str(bp.DEFAULT_RECIPE)


def _override_map(recipe):
    return {o['levelId']: o for o in recipe.get('overrides', [])
            if o.get('target') == 'wave' and o.get('field') == 'targetEhp' and o.get('scope') == 'level'}


def cmd_report(args):
    run = pathlib.Path(args.run)
    summary = json.loads((run / 'gate-summary.json').read_text(encoding='utf-8'))
    rows = json.loads((run / 'gate-matrix.json').read_text(encoding='utf-8'))
    by_level = {}
    for row in rows:
        by_level.setdefault(row['levelId'], {})[(row['mode'], round(row['mazeFraction'], 2))] = row
    print('| 关 | 0.50 | 0.70 | 0.85 | 1.00 | no_up | G4 明细 | 动作 |')
    print('|---|---|---|---|---|---|---|---|')
    for level in sorted(by_level):
        item = by_level[level]
        def cell(key):
            row = item.get(key)
            if not row:
                return '—'
            return '%d/%d' % (row['leaked'], row['hp'])
        detail = summary['levels'][str(level)].get('detail', {}).get('G4', {})
        g4 = 'clear=%s pol=%s bud=%s t=%s r=%.3f' % (
            detail.get('clear'), detail.get('policy'), detail.get('budget'),
            detail.get('time'), detail.get('ratio', 0)) if detail else '—'
        print('| %d | %s | %s | %s | %s | %s | %s | %s |' % (
            level, cell(('fill', 0.5)), cell(('fill', 0.7)), cell(('fill', 0.85)),
            cell(('fill', 1.0)), cell(('no_upgrade', 1.0)), g4,
            summary['levels'][str(level)].get('action', '—')))
    print('\npassed=%s failing=%s' % (summary['passed'], summary['failingLevels']))
    return 0


def repair_monotonic(recipe, max_rounds=40, bump=1.015):
    """Raise offending levels until every wave's EHP strictly increases across levels."""
    for _ in range(max_rounds):
        plan = bp.generate(recipe, recipe.get('selectedProfileId', 'D04'))
        errors = bp.validate(plan)['errors']
        if not errors:
            return recipe, 0
        bad = {int(e.split('L')[1].split()[0]) for e in errors if 'EHP not strictly increasing L' in e}
        if not bad:
            raise RuntimeError('non-monotonic validation errors: ' + '; '.join(errors[:3]))
        ov = _override_map(recipe)
        for level in bad:
            if level in ov:
                ov[level]['value'] = round(ov[level]['value'] * bump, 4)
    raise RuntimeError('monotonic repair did not converge')


def cmd_adjust(args):
    recipe = bp.read_json(args.recipe)
    ov = _override_map(recipe)
    changed = {}
    for item in args.mult.split(','):
        if not item.strip():
            continue
        level, mult = item.split(':')
        level, mult = int(level), float(mult)
        if level not in ov:
            raise RuntimeError('level %d has no targetEhp override' % level)
        ov[level]['value'] = round(ov[level]['value'] * mult, 4)
        changed[level] = round(mult, 4)
    recipe, rounds = repair_monotonic(recipe)
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(recipe, ensure_ascii=False, indent=2), encoding='utf-8')
    if args.write:
        pathlib.Path(DEFAULT_RECIPE).write_text(json.dumps(recipe, ensure_ascii=False, indent=2), encoding='utf-8')
    plan = bp.generate(recipe, recipe.get('selectedProfileId', 'D04'))
    print(json.dumps({'event': 'adjust', 'changed': changed, 'repairRounds': rounds,
                      'validate': bp.validate(plan)['passed'], 'written': str(out)}))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('report')
    p.add_argument('--run', required=True)
    p = sub.add_parser('adjust')
    p.add_argument('--recipe', default=DEFAULT_RECIPE)
    p.add_argument('--out', required=True)
    p.add_argument('--mult', required=True, help='level:multiplier, comma separated')
    p.add_argument('--write', action='store_true', default=False)
    args = parser.parse_args(argv)
    if args.command == 'report':
        return cmd_report(args)
    return cmd_adjust(args)


if __name__ == '__main__':
    raise SystemExit(main())
