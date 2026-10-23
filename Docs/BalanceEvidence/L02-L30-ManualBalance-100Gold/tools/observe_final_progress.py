"""Read live completed results; never archive or certify a still-running batch."""
from formal_tools import *
from compare_replays import compare
import sys, collections

tag=sys.argv[1]; folder=ROOT/'Library/BalanceWorkbench'/tag
status=json.loads((folder/'status.json').read_text(encoding='utf-8'))
rows=json.loads((folder/'unity-results.json').read_text(encoding='utf-8'))
print('Batch',tag,status['phase'],status['completed'],'/',status['total'],
      'current L',status.get('current',{}).get('levelId'),'W',status.get('round'))
groups=collections.defaultdict(list)
for row in rows:
    if row['strategy'].startswith('final-reference-'):groups[row['levelId']].append(row)
print('Completed strict triples:',[(level,compare(group)['allMatch'])
                                  for level,group in sorted(groups.items()) if len(group)==3])
print('Latest actual outcomes:',[(r['levelId'],r['strategy'],r['stars'],r['metrics']['leaked'],r['state'])
                                for r in rows[-4:]])
