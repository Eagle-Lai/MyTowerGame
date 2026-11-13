import fs from 'node:fs/promises';
import path from 'node:path';
import {FileBlob,SpreadsheetFile} from '@oai/artifact-tool';
const root=path.resolve('.'),manifest=JSON.parse(await fs.readFile(process.argv[2],'utf8'));
const out=path.resolve(process.argv[3]||'Library/BalanceStage/trusted-terminal-design-20261109/source-authoring');
await fs.mkdir(out,{recursive:true});
for(const name of [...new Set(manifest.edits.map(e=>e.table))]){
 const source=path.join(root,'Luban/Config/Datas/Levels/L02',name+'.xlsx');
 const edits=manifest.edits.filter(e=>e.table===name&&JSON.stringify(e.old)!==JSON.stringify(e.value));
 const book=await SpreadsheetFile.importXlsx(await FileBlob.load(source)),sheet=book.worksheets.getItemAt(0);
 const values=sheet.getUsedRange().values, headers=new Map(values[0].map((h,i)=>[h,i]));
 const positions=new Map(values.map((r,i)=>[r[headers.get('id')],i]));
 const stringify=v=>Array.isArray(v)?v.join(','):v;
 const changedRows=edits.map(e=>positions.get(e.id)+1);
 if(changedRows.some(n=>!Number.isFinite(n)))throw Error('Missing changed row');
 const first=Math.max(1,Math.min(...changedRows)-1),last=Math.max(...changedRows)+1;
 const viewRange=`B${first}:${name==='EnemyData'?'J':name==='EnemyList'?'F':'G'}${last}`;
 const rendered=await book.render({sheetName:sheet.name,range:viewRange,scale:1,format:'png'});
 await fs.writeFile(path.join(out,name+'-before.png'),new Uint8Array(await rendered.arrayBuffer()));
 for(const e of edits){
  const row=positions.get(e.id),col=headers.get(e.field);
  if(row===undefined||row<3||col===undefined)throw Error('Cell not found '+JSON.stringify(e));
  const old=stringify(e.old),value=stringify(e.value);
  if(values[row][col]!==old)throw Error('Unexpected old value '+name+' '+e.id+' '+e.field);
  e.sheet=sheet.name;e.row=row+1;e.col=col+1;
  sheet.getCell(row,col).values=[[value]];
 }
 book.recalculate();
 for(const e of edits){if(sheet.getCell(e.row-1,e.col-1).values[0][0]!==stringify(e.value))throw Error('Readback failed');}
 const after=await book.render({sheetName:sheet.name,range:viewRange,scale:1,format:'png'});
 await fs.writeFile(path.join(out,name+'-after.png'),new Uint8Array(await after.arrayBuffer()));
 await (await SpreadsheetFile.exportXlsx(book)).save(path.join(out,name+'.xlsx'));
 console.log(JSON.stringify({table:name,authoredCells:edits.length}));
}
await fs.writeFile(path.join(out,'located-manifest.json'),JSON.stringify(manifest,null,2));
process.exit(0);
