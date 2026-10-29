import fs from 'node:fs'; import path from 'node:path';
const root='Library/BalanceStage/all_profiles_v2';
for(const d of fs.readdirSync(root).sort()){
 const j=JSON.parse(fs.readFileSync(path.join(root,d,'ConfigJson','tbtowerinfo.json'),'utf8'));
 console.log(d, j.map(r=>[r.id,r.power,r.CD,r.radius,r.prices,r.effectValue,r.sellPrice]).map(x=>x.join(':')).join(' | '));
}
