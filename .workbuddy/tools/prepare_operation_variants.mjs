#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1')), '../..');
const simRoot = path.join(root, 'Library', 'BalanceStage', 'sim');
const profiles = Array.from({ length: 8 }, (_, i) => `D${String(i + 1).padStart(2, '0')}`);
const scenarios = ['ehp95', 'ehp105', 'drop05', 'drop10', 'power70', 'power50', 'noUpgrade'];
for (const scenario of scenarios) fs.rmSync(path.join(simRoot, `gold100_ops_${scenario}`), { recursive: true, force: true });
const manifest = [];
for (const profile of profiles) {
  const baseDir = path.join(simRoot, `gold100_base_${profile}`);
  for (let level = 1; level <= 30; level++) {
    const file = path.join(baseDir, `L${String(level).padStart(2, '0')}.json`);
    const base = JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, ''));
    const ops = Array.isArray(base.operations) ? base.operations : [];
    const builds = ops.filter((op) => op.type === 'build');
    const remove = (ratio) => {
      const n = Math.ceil(builds.length * ratio);
      const coords = new Set(builds.slice(-n).map((op) => `${op.x},${op.y}`));
      return ops.filter((op) => !coords.has(`${op.x},${op.y}`));
    };
    const variants = {
      ehp95: ops,
      ehp105: ops,
      drop05: remove(0.05),
      drop10: remove(0.10),
      power70: ops,
      power50: ops,
      noUpgrade: ops.filter((op) => op.type !== 'upgrade'),
    };
    for (const scenario of scenarios) {
      const dir = path.join(simRoot, `gold100_ops_${scenario}`, profile);
      fs.mkdirSync(dir, { recursive: true });
      const variantOps = variants[scenario];
      fs.writeFileSync(path.join(dir, `L${String(level).padStart(2, '0')}.json`), `${JSON.stringify({
        schema: 'balance_operation_script/1', profileId: profile, levelId: level,
        source: `gold100_base_${profile}/L${String(level).padStart(2, '0')}.json`,
        baselineOperationCount: ops.length, operationCount: variantOps.length,
        baselineBuildCount: builds.length,
        removedBuildCount: scenario === 'drop05' ? builds.length - variantOps.filter((op) => op.type === 'build').length : scenario === 'drop10' ? builds.length - variantOps.filter((op) => op.type === 'build').length : 0,
        operations: variantOps,
      }, null, 2)}\n`, 'utf8');
    }
    manifest.push({ profileId: profile, levelId: level, baselineOperations: ops.length, baselineBuilds: builds.length,
      ehp95: ops.length, ehp105: ops.length, drop05: variants.drop05.length, drop10: variants.drop10.length,
      power70: ops.length, power50: ops.length, noUpgrade: variants.noUpgrade.length });
  }
}
fs.writeFileSync(path.join(simRoot, 'gold100_operation_variants.json'), `${JSON.stringify({ schema: 'balance_operation_variants/1', scenarios, rows: manifest }, null, 2)}\n`, 'utf8');
console.log(JSON.stringify({ scenarios, rows: manifest.length }, null, 2));
