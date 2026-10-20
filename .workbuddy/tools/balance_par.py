"""Par calibration for the fill-gate reference garrison.

Order matters: the numbers must be frozen first, because combatBasisHash covers
targetEhp / towers / bullets / map / timing. Write the Par values last, then prove
that generate() picks every one of them up (parCalibrationCurrent) before the
recipe is published to apply.
"""
import argparse, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import balance_pipeline as bp

DEFAULT_RECIPE = str(bp.DEFAULT_RECIPE)


def load_full_rows(run):
    rows = json.loads((pathlib.Path(run) / 'gate-matrix.json').read_text(encoding='utf-8'))
    return {r['levelId']: r for r in rows
            if abs(r['mazeFraction'] - 1.0) < 1e-9 and r['mode'] == 'fill'}


def cmd_calibrate(args):
    recipe = bp.read_json(args.recipe)
    if recipe.get('parCalibration'):
        if not args.force:
            raise RuntimeError('parCalibration is not empty; freeze numbers first or pass --force')
        recipe['parCalibration'] = {}
    profile = recipe.get('selectedProfileId', 'D04')
    plan = bp.generate(recipe, profile)
    if any(l.get('parCalibrationCurrent') for l in plan['levels']):
        raise RuntimeError('expected every level to be uncalibrated before writing')

    full = load_full_rows(args.run)
    hashes = {l['levelId']: l['combatBasisHash'] for l in plan['levels']}
    entries, skipped = {}, {}
    for level in range(1, plan['levelCount'] + 1):
        row = full.get(level)
        if not row:
            skipped[level] = 'no full-maze row'
            continue
        if row.get('combatBasisHash') and row['combatBasisHash'] != hashes[level]:
            skipped[level] = 'stale run (recipe changed after the measurement)'
            continue
        if not (row['victory'] and row['leaked'] == 0 and row['builtCount'] >= row['targetTowers'] - 1):
            skipped[level] = 'reference garrison not clean (leaked=%d, built=%d/%d)' % (
                row['leaked'], row['builtCount'], row['targetTowers'])
            continue
        par = int(round(row['combatMs'] * args.factor / 1000.0)) * 1000
        entries[str(level)] = {
            'combatBasisHash': hashes[level],
            'parCombatTimeMs': par,
            'method': 'offline fill-gate full-maze reference garrison; uniform upgrade budget; '
                      '%dms step; x%.2f; rounded to 1s' % (args.step_ms, args.factor),
            'observedCombatMs': row['combatMs'],
        }
    if not entries:
        raise RuntimeError('no calibratable levels; check the run directory')
    recipe['parCalibration'] = {profile: entries}

    plan2 = bp.generate(recipe, profile)
    current = [l['levelId'] for l in plan2['levels'] if l.get('parCalibrationCurrent')]
    stale = [l for l in entries if int(l) not in current]
    if stale:
        raise RuntimeError('parCalibration did not bind for levels %s (hash mismatch)' % stale)
    validation = bp.validate(plan2)
    if not validation['passed']:
        raise RuntimeError('validate failed after Par write: ' + '; '.join(validation['errors'][:3]))

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(recipe, ensure_ascii=False, indent=2), encoding='utf-8')
    if args.write:
        pathlib.Path(DEFAULT_RECIPE).write_text(json.dumps(recipe, ensure_ascii=False, indent=2), encoding='utf-8')
    report = {'profileId': profile, 'factor': args.factor, 'calibrated': sorted(int(k) for k in entries),
              'skipped': {str(k): v for k, v in skipped.items()},
              'parCalibrationCurrent': len(current), 'entries': entries}
    pathlib.Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'event': 'par', 'calibrated': len(entries), 'skipped': len(skipped),
                      'current': len(current), 'validate': True, 'written': str(out)}))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('calibrate')
    p.add_argument('--run', required=True)
    p.add_argument('--recipe', default=DEFAULT_RECIPE)
    p.add_argument('--out', required=True)
    p.add_argument('--report', default='Luban/BalanceDesign/FillGate/par-report.json')
    p.add_argument('--factor', type=float, default=1.06)
    p.add_argument('--step-ms', type=int, default=100)
    p.add_argument('--write', action='store_true', default=False)
    p.add_argument('--force', action='store_true', default=False)
    args = parser.parse_args(argv)
    return cmd_calibrate(args)


if __name__ == '__main__':
    raise SystemExit(main())
