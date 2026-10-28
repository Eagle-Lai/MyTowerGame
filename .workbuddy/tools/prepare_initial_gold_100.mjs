#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1')), '../..');
const sourceRoot = path.join(root, 'Library', 'BalanceStage', 'replay_current');
const outRoot = path.join(root, 'Library', 'BalanceStage', 'initial_gold_100');
const profiles = Array.from({ length: 8 }, (_, i) => `D${String(i + 1).padStart(2, '0')}`);

fs.rmSync(outRoot, { recursive: true, force: true });
fs.mkdirSync(outRoot, { recursive: true });
const checks = [];
for (const profile of profiles) {
  const src = path.join(sourceRoot, profile);
  const dst = path.join(outRoot, profile);
  if (!fs.existsSync(src)) throw new Error(`missing staging source: ${src}`);
  fs.cpSync(src, dst, { recursive: true });
  const scenePath = path.join(dst, 'tbsceneinfo.json');
  const scenes = JSON.parse(fs.readFileSync(scenePath, 'utf8').replace(/^\uFEFF/, ''));
  for (const row of scenes) row.initialGold = 100;
  fs.writeFileSync(scenePath, `${JSON.stringify(scenes, null, 2)}\n`, 'utf8');
  const bad = scenes.filter((row) => row.initialGold !== 100).map((row) => row.id);
  if (bad.length) throw new Error(`${profile}: InitialGold assertion failed for ${bad.join(',')}`);
  checks.push({ profileId: profile, levels: scenes.length, initialGold: 100, source: path.relative(root, src).replaceAll('\\', '/'), output: path.relative(root, dst).replaceAll('\\', '/') });
}
fs.writeFileSync(path.join(outRoot, 'manifest.json'), `${JSON.stringify({ schema: 'balance_initial_gold_100/1', checks }, null, 2)}\n`, 'utf8');
console.log(JSON.stringify({ outRoot, profiles: checks.length, levels: checks.reduce((n, x) => n + x.levels, 0), initialGold: 100 }, null, 2));
