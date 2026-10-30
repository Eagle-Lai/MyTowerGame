from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json
HERE=Path(__file__).resolve().parent
RUN=HERE.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
result=json.loads((HERE/'generation/Down/revision_03/result.json').read_text())
assert result['status']==200 and (HERE/'generation/Down/revision_03/raw.png').stat().st_size==result['bytes']
assert not (HERE/'staged_art').exists() and not (HERE/'art_selection.json').exists()
up={
 'HeadNormal':[25,90,360,470], 'HeadAngry':[405,90,745,470], 'HeadDead':[790,90,1125,470],
 'Body':[1160,65,1500,520], 'LegFront':[85,580,300,920], 'LegBack':[450,580,700,930],
 'Tail':[755,550,1100,935]
}
down={
 'HeadNormal':[10,55,370,485], 'HeadAngry':[390,55,770,485], 'HeadDead':[775,55,1145,490],
 'Body':[15,510,355,965], 'LegFront':[450,565,650,940], 'LegBack':[680,585,900,930],
 'Tail':[905,555,1190,930]
}
selection={'Up':'generation/Up/local_revision_03/raw.png','Down':'generation/Down/revision_03/raw.png',
 'rectangles':{**{'Up_'+k:v for k,v in up.items()},**{'Down_'+k:v for k,v in down.items()}},
 'note':'Actual full raw images reviewed. Down03 inserted an unwanted fourth rear head in top-right; it remains in raw history but is excluded. Body and legs are selected from their actual lower-row positions, tail crosses the nominal cell boundary. Up03 is documented local raster, not new AI output.',
 'source_sha256':{'Up':sha(HERE/'generation/Up/local_revision_03/raw.png'),'Down':sha(HERE/'generation/Down/revision_03/raw.png')}}
(HERE/'art_selection.json').write_text(json.dumps(selection,indent=2)+'\n',encoding='utf-8')
parts={
 'Up/Body':dict(y=.51,width=.69,height=.72),
 'Up/Head':dict(y=.81,width=.68,height=.63,order=30),
 'Up/Tail':dict(x=-.01,y=.38,width=.24,height=.40,order=31,angle=0),
 'Down/Body':dict(y=.63,width=.70,height=.72),
 'Down/Head':dict(y=.44,width=.72,height=.67),
 'Down/Tail':dict(x=.12,y=.88,width=.24,height=.38,order=5,angle=-20),
}
for direction in ['Up','Down']:
 for side,sign in [('L',-1),('R',1)]:
  parts[f'{direction}/Fore{side}']=dict(x=sign*.135,y=.60 if direction=='Up' else .36,width=.175,height=.28 if direction=='Up' else .31,angle=sign*(24 if direction=='Up' else 6))
  parts[f'{direction}/Hind{side}']=dict(x=sign*.145,y=.34 if direction=='Up' else .71,width=.18,height=.31 if direction=='Up' else .28,angle=sign*(5 if direction=='Up' else 25))
layout={'reason':'Measured from this pointed-ear, white-ruff, spotted WinterWolfTypeA source and its reviewed raw parts. Axial head retains the original large-head silhouette; far shoulder/hip roots buried into torso, four short legs with opposite diagonal phases and restrained bush-tail swing.',
 'layout':{'motion':{'legAngle':7.5,'legLift':.024,'bodyBob':.006,'bodyRoll':.65,'tailSwing':5}},
 'parts':parts,'sprites':{f'{d}_{role}':{'pivotX':.5,'pivotY':.94} for d in ['Up','Down'] for role in ['LegFront','LegBack']}}
layout['sprites'].update({'Up_Tail':{'pivotX':.06,'pivotY':.80},'Down_Tail':{'pivotX':.05,'pivotY':.94}})
(HERE/'layout_adjustments.json').write_text(json.dumps(layout,indent=2)+'\n',encoding='utf-8')
record={'observed_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'current_stage':'Down03_HTTP200_raw_reviewed_before_stage','old_unknown_requests':3,'standing_recovery_used':2,'additional_current_turn_requests':1,'additional_current_turn_HTTP200':1,'edge_resolve':'191.101.132.254','user_approved':False,'extra_top_right_rear_head_excluded':True,'full_raw_reviewed':True,'stage_validation_pending':True}
(HERE/'edge_resume_success_and_raw_review_20261029.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=RUN/'progress.json';progress=json.loads(p.read_text());item=next(x for x in progress['items'] if x['name']=='WinterWolfTypeA');item.update(status='reference_prepared',current_stage='Down03_HTTP200_raw_reviewed_before_stage',edge_resume_record='Docs/EnemyDirectionReview/Remaining_20261024/WinterWolfTypeA/edge_resume_success_and_raw_review_20261029.json');progress.update(status='in_progress',updated_at=record['observed_at']);p.write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,ensure_ascii=False))
