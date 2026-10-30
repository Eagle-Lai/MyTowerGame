// AIHub is explicitly authorized by AGENTS.md. Key exists in process memory only.
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
const root=path.dirname(fileURLToPath(import.meta.url));
const [name,direction,...args]=process.argv.slice(2);
const revision=args[0]?.startsWith('revision_')?args.shift():undefined;
const artSourceOptions=args.filter(arg=>arg.startsWith('--art-source='));
if(artSourceOptions.length>1)throw new Error('Choose one successful art source revision');
const artSourceRevision=artSourceOptions.length?artSourceOptions[0].slice('--art-source='.length):undefined;
if(artSourceOptions.length)args.splice(args.indexOf(artSourceOptions[0]),1);
if(artSourceRevision&&!/^revision_\d\d$/.test(artSourceRevision))throw new Error('Invalid art source revision');
if(args.some(arg=>!['--recover-failed','--authorized-uncertain-retry','--authorized-network-recovery','--authorized-resume','--curl-transport','--system-local-proxy','--preflight'].includes(arg))||new Set(args).size!==args.length)throw new Error('Invalid generation option');
const recoverFailed=args.includes('--recover-failed');
const authorizedUncertainRetry=args.includes('--authorized-uncertain-retry');
const authorizedNetworkRecovery=args.includes('--authorized-network-recovery');
const authorizedResume=args.includes('--authorized-resume');
const curlTransport=args.includes('--curl-transport')||authorizedResume;
const systemLocalProxy=args.includes('--system-local-proxy');
if(systemLocalProxy){
 const winterOgreProxy=name==='WinterOgre'&&(direction==='Up'&&revision==='revision_04'||direction==='Down'&&!revision);
 const winterWargProxy=name==='WinterWarg'&&direction==='Up'&&['revision_01','revision_02'].includes(revision)&&authorizedNetworkRecovery;
 const winterWolfTypeAProxy=name==='WinterWolfTypeA'&&direction==='Down'&&revision==='revision_02'&&authorizedNetworkRecovery;
 if(!curlTransport||!winterOgreProxy&&!winterWargProxy&&!winterWolfTypeAProxy)throw new Error('Local proxy scope requires a reviewed character transport application');
 const chain=JSON.parse(fs.readFileSync(path.join(root,'conversation_chain.json'),'utf8'));
 if(chain.state!=='active'||chain.current_character!==name||chain.owner_thread_id!==process.env.CODEX_THREAD_ID)throw new Error('Proxy transport requires the active serial owner');
 if(winterWolfTypeAProxy){
  const controlFile=path.join(root,name,'unauthenticated_transport_control_20261029.json');
  const application=JSON.parse(fs.readFileSync(path.join(root,name,'proxy_transport_application_20261029.json'),'utf8'));
  const control=JSON.parse(fs.readFileSync(controlFile,'utf8'));
  const proxy=control.controls.find(c=>c.route==='existing_local_proxy');
  const metrics=JSON.parse(proxy?.stdout.match(/CONTROL_METRICS=(\{.*\})/)?.[1]||'null');
  if(application.owner_thread_id!==chain.owner_thread_id||application.dispatch_token!==chain.dispatch_token||application.control_sha256!==createHash('sha256').update(fs.readFileSync(controlFile)).digest('hex')||control.credential_present!==false||control.new_paid_diagnostic_requests!==0||proxy?.exit_code!==0||metrics?.http_status!==401||metrics.uploaded<400000||metrics.tls_verify!==0)throw new Error('Current proxy application needs matching complete-upload unauthenticated401 evidence');
 }
}
if([recoverFailed,authorizedUncertainRetry,authorizedNetworkRecovery,authorizedResume,!!artSourceRevision].filter(Boolean).length>1)throw new Error('Choose exactly one recovery or art-correction mode');
const preflight=args.includes('--preflight');
if(!/^[A-Za-z]+$/.test(name??'')||!['Up','Down'].includes(direction))throw new Error('Use character name and Up/Down');
if(revision&&!/^revision_\d\d$/.test(revision))throw new Error('Invalid revision');
if(recoverFailed&&!revision)throw new Error('Failed-request recovery requires a fresh revision');
const dir=path.join(root,name,'generation',direction,...(revision?[revision]:[]));
const output=path.join(dir,'raw.png');
if(fs.existsSync(output))throw new Error('Output already exists; a paid request will not be repeated.');
if(fs.existsSync(path.join(dir,'request.json')))throw new Error('Prior request exists. Inspect its result before any retry.');
if(['result.json','uncertain_result.json'].some(file=>fs.existsSync(path.join(dir,file))))throw new Error('Prior outcome exists; use an unused revision.');
const target=JSON.parse(fs.readFileSync(path.join(root,'local_baseline.json'),'utf8')).targets.find(t=>t.name===name);
if(!target)throw new Error('Character is not in the authorized baseline');
const inputs=[path.join(root,name,'reference',path.basename(target.atlas)),path.join(root,name,'reference','source_prefab_offline.png')];
const sha=file=>createHash('sha256').update(fs.readFileSync(file)).digest('hex');
let recovery,artRevision,verifiedDirectTransport=false;
if(authorizedResume&&name==='PossessedWarg'){
 if(direction!=='Down'||revision!=='revision_01'||!curlTransport||systemLocalProxy)throw new Error('PossessedWarg resume is Down revision_01, direct Curl only');
 const authorizationFile=path.join(root,name,'authorized_resume_20261030.json');
 const authorization=JSON.parse(fs.readFileSync(authorizationFile,'utf8'));
 const intentFile=path.join(dir,'recovery_intent.json');
 const intent=JSON.parse(fs.readFileSync(intentFile,'utf8'));
 const chain=JSON.parse(fs.readFileSync(path.join(root,'conversation_chain.json'),'utf8'));
 const token='zombie-to-possessedwarg-20261030_092519-e9c91d1a-28d7-428f-ac88-9ea00046da2b';
 if(chain.state!=='active'||chain.current_character!==name||chain.owner_thread_id!==process.env.CODEX_THREAD_ID||chain.dispatch_token!==token||authorization.owner_thread_id!==chain.owner_thread_id||authorization.dispatch_token!==token||intent.owner_thread_id!==chain.owner_thread_id||intent.dispatch_token!==token)throw new Error('PossessedWarg resume requires its actual active owner and exact dispatch token');
 const projectRoot=path.resolve(root,'../../..');
 const evidencePath=p=>{const absolute=path.resolve(projectRoot,p);if(!absolute.startsWith(projectRoot+path.sep))throw new Error('Evidence path outside project');return absolute;};
 const equalSha=(file,expected)=>sha(file).toUpperCase()===expected?.toUpperCase();
 const decisionFile=evidencePath(authorization.parent_decision_file);
 const decision=JSON.parse(fs.readFileSync(decisionFile,'utf8'));
 const originalListFile=evidencePath(decision.preserved_evidence_file);
 const originals=JSON.parse(fs.readFileSync(originalListFile,'utf8'));
 const originalMessages=evidencePath(decision.standing_original_messages_file);
 const messages=JSON.parse(fs.readFileSync(originalMessages,'utf8'));
 const originalText=JSON.stringify(messages);
 const parameters={endpoint:'https://aihub.dog/v1/images/edits',model:'gpt-image-2',quality:'medium',size:'1536x1024',n:1};
 if(!equalSha(decisionFile,authorization.parent_decision_sha256)||!equalSha(originalListFile,decision.preserved_evidence_sha256)||!equalSha(originalMessages,decision.standing_original_messages_sha256)||!equalSha(evidencePath(decision.standing_recovery_record),decision.standing_recovery_record_sha256)||!originalText.includes('01a180aa-7768-7222-bc85-7aa51e801cdd')||!originalText.includes('继续任务。后续同样的情况，不再需要我确认，可以继续静默执行'))throw new Error('PossessedWarg parent decision or original standing evidence drift');
 if(decision.character!==name||decision.direction!==direction||decision.revision!==revision||decision.planned_dispatch_token!==token||decision.max_requests!==1||decision.original_outcome!=='unknown'||decision.original_possible_charge!=='unknown'||decision.resets_automatic_counter!==false||JSON.stringify(decision.parameters)!==JSON.stringify(parameters))throw new Error('Invalid once-only parent decision; original outcome and charge stay unknown');
 if(authorization.user_statement!=='继续任务'||authorization.max_requests!==1||authorization.character!==name||authorization.direction!==direction||authorization.revision!==revision||authorization.transport!=='curl_https_no_retry'||authorization.force_direct!==true||authorization.edge_ip!=='191.101.132.254'||authorization.accept_possible_duplicate_charge!==true||authorization.original_outcome!=='unknown'||authorization.original_possible_charge!=='unknown'||authorization.resets_automatic_counter!==false||JSON.stringify(authorization.parameters)!==JSON.stringify(parameters)||!equalSha(fileURLToPath(import.meta.url),authorization.generator_sha256))throw new Error('PossessedWarg current authorization scope or generator fingerprint mismatch');
 if(!equalSha(authorizationFile,intent.authorization_sha256)||intent.parent_decision_sha256!==authorization.parent_decision_sha256||intent.max_requests!==1||intent.character!==name||intent.direction!==direction||intent.revision!==revision||intent.generator_sha256!==authorization.generator_sha256||intent.original_outcome!=='unknown'||intent.original_possible_charge!=='unknown'||JSON.stringify(intent.protected_six)!==JSON.stringify(decision.protected_six)||JSON.stringify(intent.preserved_evidence)!==JSON.stringify(originals))throw new Error('PossessedWarg intent fingerprint mismatch');
 if(Object.keys(originals).length!==21||Object.keys(decision.protected_six).length!==6)throw new Error('PossessedWarg needs the complete original evidence and six source protections');
 for(const [p,s] of Object.entries(originals))if(!equalSha(path.join(root,name,p),s))throw new Error('Original PossessedWarg evidence changed: '+p);
 for(const [p,s] of Object.entries(decision.protected_six))if(!equalSha(evidencePath(p),s))throw new Error('Protected production/source drift: '+p);
 if(!equalSha(path.join(root,name,'generation/Down/request.json'),'B2B3C9FB4B78E2FFB5E606FCE95BB2843575982CADBE6C6E97D352346D27BA4A')||!equalSha(path.join(dir,'prompt.txt'),intent.prompt_sha256)||JSON.stringify(inputs.map(p=>sha(p).toUpperCase()))!==JSON.stringify(intent.input_sha256))throw new Error('PossessedWarg request, prompt or original reference drift');
 const collect=p=>fs.readdirSync(p,{withFileTypes:true}).flatMap(e=>e.isDirectory()?collect(path.join(p,e.name)):[path.join(p,e.name)]);
 const oldDown=path.join(root,name,'generation/Down');
 if(collect(oldDown).some(p=>/\.(png|jpg|jpeg|webp)$/i.test(p)||path.basename(p)==='request.json'&&p!==path.join(oldDown,'request.json')))throw new Error('Existing Down image/request must be recovered; no further bounded request');
 const processes=spawnSync('powershell.exe',['-NoProfile','-Command',"@(Get-CimInstance Win32_Process | Where-Object { ($_.Name -eq 'node.exe' -and $_.CommandLine -match 'generate[.]mjs' -and $_.ProcessId -ne "+process.pid+") -or ($_.Name -eq 'curl.exe' -and $_.CommandLine -match 'aihub[.]dog') }).Count"],{encoding:'utf8',windowsHide:true});
 if(processes.status!==0||processes.stdout.trim()!=='0')throw new Error('Another image request is in flight or process inspection failed');
 if(!preflight){
  const unityFile=path.join(root,name,'resume_unity_preflight_20261030.json');
  const unity=JSON.parse(fs.readFileSync(unityFile,'utf8'));const age=Date.now()-Date.parse(unity.observed_at);
  if(unity.owner_thread_id!==chain.owner_thread_id||unity.dispatch_token!==token||unity.project?.projectRoot!=='E:/MyTowerGame'||unity.project?.unityVersion!=='2022.3.62f3c1'||unity.ready!==true||unity.idle!==true||unity.transport!=='http://127.0.0.1:8088/mcp'||!Number.isFinite(age)||age<0||age>120000)throw new Error('PossessedWarg needs fresh matching Unity identity, readiness and idle evidence');
  if(Object.keys(process.env).some(k=>/^(HTTP_PROXY|HTTPS_PROXY|ALL_PROXY)$/i.test(k)&&process.env[k])||process.env.NO_PROXY!=='aihub.dog')throw new Error('PossessedWarg must clear proxy variables only in the invoking process');
 }
 verifiedDirectTransport=true;
 recovery={mode:'bounded_PossessedWarg_resume_preserving_unknown_original',authorization:authorizationFile,authorization_sha256:sha(authorizationFile),intent:intentFile,intent_sha256:sha(intentFile),parent_decision:decisionFile,parent_decision_sha256:sha(decisionFile),max_requests:1,transport:'curl_https_no_retry',prior_outcome:'unknown',prior_charge:'unknown',resets_automatic_counter:false};
}else if(authorizedResume){
 const winterWolfTypeAEdgeResume=name==='WinterWolfTypeA'&&direction==='Down'&&revision==='revision_03';
 const winterOgreResume=name==='WinterOgre'&&direction==='Up'&&['revision_03','revision_04','revision_05'].includes(revision);
 const winterOgreProxyResume=winterOgreResume&&revision==='revision_04';
 const winterOgreVerifiedServiceResume=winterOgreResume&&revision==='revision_05';
 const scarabMountedResume=name==='ScarabMounted'&&direction==='Down'&&revision==='revision_03';
 if(!winterOgreResume&&!scarabMountedResume&&!winterWolfTypeAEdgeResume)throw new Error('Resume is restricted to a documented single current-turn request');
 const authorizationFile=path.join(root,name,winterWolfTypeAEdgeResume?'authorized_edge_resume_20261029.json':winterOgreVerifiedServiceResume?'authorized_verified_service_resume_20261029.json':winterOgreProxyResume?'authorized_proxy_resume_20261029.json':winterOgreResume?'authorized_resume_20261029.json':'authorized_resume_20261028.json');
 const authorization=JSON.parse(fs.readFileSync(authorizationFile,'utf8'));
 const intentFile=path.join(dir,'recovery_intent.json');
 const intent=JSON.parse(fs.readFileSync(intentFile,'utf8'));
 const chain=JSON.parse(fs.readFileSync(path.join(root,'conversation_chain.json'),'utf8'));
 if(chain.state!=='active'||chain.current_character!==name||chain.owner_thread_id!==process.env.CODEX_THREAD_ID||authorization.owner_thread_id!==chain.owner_thread_id||authorization.dispatch_token!==chain.dispatch_token)throw new Error('Resume requires active owner');
 if(authorization.user_statement!=='继续任务'||authorization.max_requests!==1||authorization.character!==name||authorization.direction!==direction||authorization.revision!==revision||authorization.transport!=='curl_https_no_retry'||authorization.accept_possible_duplicate_charge!==true)throw new Error('Missing exact bounded current-turn resume record');
 if(winterWolfTypeAEdgeResume){
  const proofFile=path.join(root,authorization.edge_assessment_file);
  const toolingFile=path.join(root,authorization.edge_tooling_file);
  const priorDirs=[path.join(root,name,'generation',direction),...['revision_01','revision_02'].map(r=>path.join(root,name,'generation',direction,r))];
  const priorRequests=priorDirs.map(p=>JSON.parse(fs.readFileSync(path.join(p,'request.json'),'utf8')));
  if(systemLocalProxy||authorization.force_direct!==true||authorization.edge_ip!=='191.101.132.254'||authorization.automatic_retries_used!==2||authorization.automatic_retry_limit!==2||authorization.resets_automatic_counter!==false||authorization.prior_unknown_requests!==3||sha(proofFile)!==authorization.edge_assessment_sha256||sha(toolingFile)!==authorization.edge_tooling_sha256||sha(fileURLToPath(import.meta.url))!==authorization.generator_sha256||priorRequests.filter(r=>r.recovery?.mode==='standing_user_authorized_network_recovery').length!==2||priorDirs.some(p=>!fs.existsSync(path.join(p,'uncertain_result.json'))))throw new Error('Edge resume needs preserved counters and the reviewed user-supplied transport fix');
  if(!preflight){
   const unity=JSON.parse(fs.readFileSync(path.join(root,name,'edge_resume_unity_preflight_20261029.json'),'utf8'));
   const age=Date.now()-Date.parse(unity.observed_at);
   if(unity.owner_thread_id!==chain.owner_thread_id||unity.dispatch_token!==chain.dispatch_token||unity.project?.projectRoot!=='E:/MyTowerGame'||unity.project?.unityVersion!=='2022.3.62f3c1'||unity.ready!==true||unity.idle!==true||!Number.isFinite(age)||age<0||age>900000)throw new Error('Fresh matching Unity identity and idle preflight required');
  }
  verifiedDirectTransport=true;
 }
 if(winterOgreResume){
  if(authorization.automatic_retries_used!==2||authorization.automatic_retry_limit!==2||authorization.resets_automatic_counter!==false)throw new Error('Original WinterOgre retry counters must remain consumed');
  if(winterOgreVerifiedServiceResume){
   const proofFile=path.join(root,name,authorization.service_assessment_file);
   const proof=JSON.parse(fs.readFileSync(proofFile,'utf8'));
   const control=proof.external_test;
   const age=Date.now()-Date.parse(control?.tested_at);
   if(systemLocalProxy||authorization.force_direct!==true||authorization.previous_bounded_resume_requests_used!==2||sha(proofFile)!==authorization.service_assessment_sha256||proof.owner_thread_id!==chain.owner_thread_id||proof.dispatch_token!==chain.dispatch_token||proof.new_paid_diagnostic_requests!==0||control?.http_status!==200||control.exit_code!==0||control.endpoint!=='https://aihub.dog/v1/images/edits'||control.model!=='gpt-image-2'||control.quality!=='medium'||control.size!=='1536x1024'||control.n!==1||control.uploaded_bytes<650000||control.downloaded_bytes<800000||!Number.isFinite(age)||age<0||age>7200000||JSON.stringify(control.input_sha256)!==JSON.stringify(inputs.map(sha))||sha(path.join(root,name,control.result_image_file))!==control.result_image_sha256)throw new Error('Verified service resume requires an actual matching authenticated image-edit200/PNG');
   if(!preflight){
    const unity=JSON.parse(fs.readFileSync(path.join(root,name,'verified_service_unity_preflight_20261029.json'),'utf8'));
    const unityAge=Date.now()-Date.parse(unity.observed_at);
    if(unity.owner_thread_id!==chain.owner_thread_id||unity.dispatch_token!==chain.dispatch_token||unity.project?.projectRoot!=='E:/MyTowerGame'||unity.project?.unityVersion!=='2022.3.62f3c1'||unity.ready!==true||unity.idle!==true||!Number.isFinite(unityAge)||unityAge<0||unityAge>900000)throw new Error('Fresh matching Unity identity and idle preflight required');
   }
   verifiedDirectTransport=true;
  }else{
   const networkFile=path.join(root,name,authorization.network_assessment_file);
   const network=JSON.parse(fs.readFileSync(networkFile,'utf8'));
   const models=network.responses.find(x=>x.url==='https://aihub.dog/v1/models');
   const usage=network.responses.find(x=>x.url.startsWith('https://aihub.dog/v1/usage?'));
   if(sha(networkFile)!==authorization.network_assessment_sha256||models?.http_status!==200||!models.image_models.includes('gpt-image-2')||usage?.http_status!==200||usage.body?.isValid!==true||!(usage.body?.balance>0))throw new Error('Missing factual bounded WinterOgre network resume assessment');
  }
  const standingFile=path.join(root,'standing_network_recovery_authorization_20261028.json');
  const standing=JSON.parse(fs.readFileSync(standingFile,'utf8'));
  if(sha(standingFile)!==authorization.standing_authorization_sha256||standing.accept_possible_duplicate_charge!==true||standing.max_additional_network_retries_per_direction!==2)throw new Error('Standing recovery evidence drift');
  if(winterOgreProxyResume){
   const proofFile=path.join(root,name,authorization.proxy_control_file);
   const proof=JSON.parse(fs.readFileSync(proofFile,'utf8'));
   const metrics=JSON.parse(proof.stdout.match(/UNAUTH_METRICS=(\{.*\})/)?.[1]||'null');
   if(!systemLocalProxy||sha(proofFile)!==authorization.proxy_control_sha256||proof.credential_present!==false||proof.process_exit!==0||metrics?.http_status!==401||metrics.uploaded<600000||metrics.tls_verify!==0||authorization.previous_current_turn_request_used!==1||authorization.use_system_local_proxy!==true)throw new Error('Proxy resume lacks actual unauthenticated complete-upload evidence');
  }
 }
 if(intent.authorization_sha256!==sha(authorizationFile)||intent.max_requests!==1||intent.character!==name||intent.direction!==direction||intent.revision!==revision)throw new Error('Resume intent fingerprint mismatch');
 for(const e of authorization.preserved_evidence){if(sha(path.join(root,name,e.path))!==e.sha256)throw new Error('Resume preserved evidence drift');}
 const parent=path.join(root,name,'generation',direction);
 if([parent,...fs.readdirSync(parent,{withFileTypes:true}).filter(e=>e.isDirectory()).map(e=>path.join(parent,e.name))].some(p=>fs.existsSync(path.join(p,'raw.png'))))throw new Error('Successful directional image must be reused');
 recovery={mode:winterWolfTypeAEdgeResume?'bounded_resume_after_user_edge_resolve_fix':winterOgreVerifiedServiceResume?'bounded_resume_after_verified_authenticated_service_recovery':'current_turn_bounded_resume_after_transport_diagnosis',authorization:authorizationFile,authorization_sha256:sha(authorizationFile),intent:intentFile,intent_sha256:sha(intentFile),max_requests:1,transport:'curl_https_no_retry',prior_outcomes:'uncertain_preserved'};
}else if(artSourceRevision){
 if(!revision||revision===artSourceRevision)throw new Error('Art correction requires a fresh output revision');
 const chain=JSON.parse(fs.readFileSync(path.join(root,'conversation_chain.json'),'utf8'));
 const intentFile=path.join(dir,'art_revision_intent.json');
 const intent=JSON.parse(fs.readFileSync(intentFile,'utf8'));
 if(chain.state!=='active'||chain.current_character!==name||chain.owner_thread_id!==process.env.CODEX_THREAD_ID||intent.owner_thread_id!==chain.owner_thread_id||intent.dispatch_token!==chain.dispatch_token)throw new Error('Art correction requires active serial owner');
 const sourceDir=path.join(root,name,'generation',direction,artSourceRevision);
 const raw=path.join(sourceDir,'raw.png'),resultFile=path.join(sourceDir,'result.json');
 const result=JSON.parse(fs.readFileSync(resultFile,'utf8'));
 if(result.status!==200||result.bytes!==fs.statSync(raw).size||intent.source_raw_sha256!==sha(raw)||intent.source_result_sha256!==sha(resultFile))throw new Error('Successful art source fingerprint mismatch');
 if(intent.character!==name||intent.direction!==direction||intent.revision!==revision||intent.source_revision!==artSourceRevision||intent.max_requests!==1||!intent.visual_finding||!intent.correction)throw new Error('Missing reviewed correction intent');
 inputs.push(raw);
 artRevision={mode:'reviewed_art_correction_reuse_success',source_revision:artSourceRevision,source_raw_sha256:sha(raw),source_result_sha256:sha(resultFile),intent:intentFile,intent_sha256:sha(intentFile)};
}else if(authorizedNetworkRecovery){
 if(!revision)throw new Error('Authorized network recovery requires a fresh revision');
 const authorizationFile=path.join(root,'standing_network_recovery_authorization_20261028.json');
 const authorization=JSON.parse(fs.readFileSync(authorizationFile,'utf8'));
 const intentFile=path.join(dir,'recovery_intent.json');
 const intent=JSON.parse(fs.readFileSync(intentFile,'utf8'));
 const chain=JSON.parse(fs.readFileSync(path.join(root,'conversation_chain.json'),'utf8'));
 if(chain.state!=='active'||chain.current_character!==name||chain.owner_thread_id!==process.env.CODEX_THREAD_ID||intent.owner_thread_id!==chain.owner_thread_id||intent.dispatch_token!==chain.dispatch_token)throw new Error('Network recovery requires the active serial owner');
 if(authorization.user_statement!=='继续任务。后续同样的情况，不再需要我确认，可以继续静默执行'||authorization.accept_possible_duplicate_charge!==true||authorization.chain_id!==chain.chain_id||authorization.max_additional_network_retries_per_direction!==2)throw new Error('Missing standing user network-recovery authorization');
 if(intent.authorization_sha256!==sha(authorizationFile)||intent.character!==name||intent.direction!==direction||intent.revision!==revision||intent.max_requests!==1||!(intent.prior_revision==='initial'||/^revision_\d\d$/.test(intent.prior_revision??'')))throw new Error('Invalid authorized recovery intent');
 const parent=path.join(root,name,'generation',direction);
 const priorDir=intent.prior_revision==='initial'?parent:path.join(parent,intent.prior_revision);
 if(sha(path.join(priorDir,'request.json'))!==intent.prior_request_sha256||sha(path.join(priorDir,'uncertain_result.json'))!==intent.prior_uncertain_sha256||sha(path.join(priorDir,'console.txt'))!==intent.prior_console_sha256)throw new Error('Preserved network evidence fingerprint mismatch');
 const uncertain=JSON.parse(fs.readFileSync(path.join(priorDir,'uncertain_result.json'),'utf8'));
 const consoleText=fs.readFileSync(path.join(priorDir,'console.txt'),'utf8');
 const beforeTlsReset=uncertain.message==='fetch failed'&&consoleText.includes('ECONNRESET')&&consoleText.includes('before secure TLS connection was established');
 let applicationEvidence;
 if(!beforeTlsReset){
  // The original human reply covered uncertain network failures and possible duplicate billing.
  // Each Curl application is restricted to its own recorded character/direction/failure.
  const tigerCurl55=name==='Tiger'&&direction==='Up'&&['revision_01','revision_02'].includes(revision)&&uncertain.message.startsWith('curl transport failed 55 curl: (55) Send failure: Connection was aborted')&&consoleText.includes('curl: (55) Send failure: Connection was aborted');
  const treasureChestCurl56=name==='TreasureChest'&&direction==='Up'&&['revision_01','revision_02'].includes(revision)&&uncertain.message.startsWith('curl transport failed 56 curl: (56) Recv failure: Connection was reset')&&consoleText.includes('curl: (56) Recv failure: Connection was reset');
  const treasureChestCurl55=name==='TreasureChest'&&direction==='Up'&&revision==='revision_02'&&intent.prior_revision==='revision_01'&&uncertain.message.startsWith('curl transport failed 55 curl: (55) Send failure: Connection was aborted')&&consoleText.includes('curl: (55) Send failure: Connection was aborted');
  const whiteWolfCurl=name==='WhiteWolf'&&['Up','Down'].includes(direction)&&['revision_01','revision_02'].includes(revision)&&((uncertain.message.startsWith('curl transport failed 55 curl: (55) Send failure: Connection was aborted')&&consoleText.includes('curl: (55) Send failure: Connection was aborted'))||(uncertain.message.startsWith('curl transport failed 56 curl: (56) Recv failure: Connection was reset')&&consoleText.includes('curl: (56) Recv failure: Connection was reset')));
  const winterOgreCurl55=name==='WinterOgre'&&direction==='Up'&&['revision_01','revision_02'].includes(revision)&&uncertain.message.startsWith('curl transport failed 55 curl: (55) Send failure: Connection was aborted')&&consoleText.includes('curl: (55) Send failure: Connection was aborted');
  const winterWargCurl55=name==='WinterWarg'&&direction==='Up'&&['revision_01','revision_02'].includes(revision)&&uncertain.message.startsWith('curl transport failed 55 curl: (55) Send failure: Connection was aborted')&&consoleText.includes('curl: (55) Send failure: Connection was aborted');
  const winterWargCurl52=name==='WinterWarg'&&direction==='Up'&&revision==='revision_02'&&intent.prior_revision==='revision_01'&&uncertain.message.startsWith('curl transport failed 52 curl: (52) Empty reply from server')&&consoleText.includes('curl: (52) Empty reply from server');
  const winterWolfTypeACurl55=name==='WinterWolfTypeA'&&direction==='Down'&&['revision_01','revision_02'].includes(revision)&&uncertain.message.startsWith('curl transport failed 55 curl: (55) Send failure: Connection was aborted')&&consoleText.includes('curl: (55) Send failure: Connection was aborted');
  const winterWolfTypeBCurl55=name==='WinterWolfTypeB'&&direction==='Up'&&['revision_01','revision_02'].includes(revision)&&uncertain.message.startsWith('curl transport failed 55 curl: (55) Send failure: Connection was aborted')&&consoleText.includes('curl: (55) Send failure: Connection was aborted');
  if(!tigerCurl55&&!treasureChestCurl56&&!treasureChestCurl55&&!whiteWolfCurl&&!winterOgreCurl55&&!winterWargCurl55&&!winterWargCurl52&&!winterWolfTypeACurl55&&!winterWolfTypeBCurl55)throw new Error('Standing recovery is limited to a documented transient network failure');
  const applicationFile=path.join(root,name,winterWargCurl52?'standing_recovery_application_20261029_Up_r02.json':whiteWolfCurl||winterOgreCurl55||winterWargCurl55||winterWolfTypeACurl55||winterWolfTypeBCurl55?'standing_recovery_application_20261029_'+direction+'.json':'standing_recovery_application_20261028.json');
  const application=JSON.parse(fs.readFileSync(applicationFile,'utf8'));
  if(intent.application_sha256!==sha(applicationFile)||application.user_statement!==authorization.user_statement||application.source_thread_id!=='01a18093-7687-7313-aaba-7419090cc829'||application.source_user_message_id!=='01a180aa-7768-7222-bc85-7aa51e801cdd'||application.owner_thread_id!==chain.owner_thread_id||application.dispatch_token!==chain.dispatch_token||application.character!==name||application.direction!==direction||application.accept_possible_duplicate_charge!==true||application.max_additional_network_retries_per_direction!==2||application.authorization_sha256!==sha(authorizationFile))throw new Error('Missing bounded application of verified standing user authorization');
  for(const e of application.preserved_evidence)if(sha(path.join(root,name,e.path))!==e.sha256)throw new Error('Original uncertain Curl evidence drift');
  applicationEvidence={file:applicationFile,sha256:sha(applicationFile),failure_class:winterWargCurl52?'curl52_empty_reply_outcome_uncertain':uncertain.message.startsWith('curl transport failed 56')?'curl56_receive_reset_outcome_uncertain':'curl55_send_aborted_outcome_uncertain',prior_charge:'unknown_not_reclassified'};
 }
 let used=0;
 for(const prior of [parent,...fs.readdirSync(parent,{withFileTypes:true}).filter(e=>e.isDirectory()&&/^revision_\d\d$/.test(e.name)).map(e=>path.join(parent,e.name))]){
  if(prior===dir)continue;
  if(fs.existsSync(path.join(prior,'raw.png')))throw new Error('Existing directional output must be reused');
  if(!fs.existsSync(path.join(prior,'request.json')))continue;
  const req=JSON.parse(fs.readFileSync(path.join(prior,'request.json'),'utf8'));
  if(req.recovery?.mode==='standing_user_authorized_network_recovery')used++;
  if(fs.existsSync(path.join(prior,'result.json'))){const result=JSON.parse(fs.readFileSync(path.join(prior,'result.json'),'utf8'));if(!(result.status>=400&&result.status<=599&&result.error&&!result.bytes))throw new Error('A prior outcome is not an explicit failure');}
  else if(!fs.existsSync(path.join(prior,'uncertain_result.json')))throw new Error('Prior request still has no outcome; inspect before retry');
 }
 if(used>=authorization.max_additional_network_retries_per_direction)throw new Error('Bounded network retry allowance exhausted');
 recovery={mode:'standing_user_authorized_network_recovery',authorization:authorizationFile,authorization_sha256:sha(authorizationFile),intent:intentFile,intent_sha256:sha(intentFile),additional_attempt:used+1,prior_outcome:'still_uncertain_not_reclassified',...(applicationEvidence?{application:applicationEvidence}:{})};
}else if(authorizedUncertainRetry){
 // A single explicit user override, never the automatic failed-request recovery path.
 if(name!=='SabretoothTiger'||direction!=='Down'||revision!=='revision_02')throw new Error('This authorization covers only SabretoothTiger Down revision_02');
 const authorizationFile=path.join(root,name,'authorized_down_retry_20261028.json');
 const authorization=JSON.parse(fs.readFileSync(authorizationFile,'utf8'));
 const intentFile=path.join(dir,'recovery_intent.json');
 const intent=JSON.parse(fs.readFileSync(intentFile,'utf8'));
 const chain=JSON.parse(fs.readFileSync(path.join(root,'conversation_chain.json'),'utf8'));
 if(chain.state!=='active'||chain.current_character!==name||chain.owner_thread_id!==process.env.CODEX_THREAD_ID||authorization.owner_thread_id!==chain.owner_thread_id||authorization.dispatch_token!==chain.dispatch_token)throw new Error('Explicit retry requires the active owner');
 if(authorization.user_answer!=='授权补发一次 Down，上限 $0.07'||authorization.accept_possible_duplicate_charge!==true||authorization.max_requests!==1||authorization.max_cost_usd!==0.07||authorization.character!==name||authorization.direction!==direction||authorization.revision!==revision)throw new Error('Missing exact bounded user authorization');
 if(intent.authorization_sha256!==sha(authorizationFile)||intent.max_requests!==1||intent.revision!==revision||intent.character!==name||intent.direction!==direction)throw new Error('Authorization fingerprint mismatch');
 for(const evidence of authorization.prior_evidence){
  const file=path.join(root,name,evidence.path);
  if(sha(file)!==evidence.sha256)throw new Error('Preserved prior evidence changed: '+evidence.path);
 }
 const parent=path.join(root,name,'generation',direction);
 for(const prior of [parent,...fs.readdirSync(parent,{withFileTypes:true}).filter(e=>e.isDirectory()&&/^revision_\d\d$/.test(e.name)).map(e=>path.join(parent,e.name))]){
  if(prior===dir)continue;
  if(fs.existsSync(path.join(prior,'raw.png')))throw new Error('Existing Down output must be recovered instead');
  if(![parent,path.join(parent,'revision_01')].includes(prior)&&fs.existsSync(path.join(prior,'request.json')))throw new Error('Another Down request exists');
 }
 recovery={mode:'explicit_user_authorized_uncertain_retry',authorization:authorizationFile,authorization_sha256:sha(authorizationFile),intent:intentFile,intent_sha256:sha(intentFile),max_cost_usd:0.07,prior_outcome:'still_uncertain_not_reclassified'};
}else if(recoverFailed){
 const parent=path.join(root,name,'generation',direction);
 const parentRequest=path.join(parent,'request.json');
 const parentResult=path.join(parent,'result.json');
 const failed=result=>Number.isInteger(result.status)&&result.status>=400&&result.status<=599&&result.error&&!result.bytes;
 if(!fs.existsSync(parentRequest)||!fs.existsSync(parentResult))throw new Error('Recovery requires an explicit parent request and HTTP failure result');
 for(const prior of [parent,...fs.readdirSync(parent,{withFileTypes:true}).filter(entry=>entry.isDirectory()&&/^revision_\d\d$/.test(entry.name)).map(entry=>path.join(parent,entry.name))]){
  if(prior===dir)continue;
  if(fs.existsSync(path.join(prior,'raw.png'))||fs.existsSync(path.join(prior,'uncertain_result.json')))throw new Error('Recovery refused: prior output or uncertain outcome exists');
  if(fs.existsSync(path.join(prior,'request.json'))&&(!fs.existsSync(path.join(prior,'result.json'))||!failed(JSON.parse(fs.readFileSync(path.join(prior,'result.json'),'utf8')))))throw new Error('Recovery refused: a prior request has no explicit HTTP failure');
 }
 const intentFile=path.join(dir,'recovery_intent.json');
 const intent=JSON.parse(fs.readFileSync(intentFile,'utf8'));
 const chain=JSON.parse(fs.readFileSync(path.join(root,'conversation_chain.json'),'utf8'));
 if(chain.state!=='active'||chain.current_character!==name||!process.env.CODEX_THREAD_ID||chain.owner_thread_id!==process.env.CODEX_THREAD_ID||intent.owner_thread_id!==chain.owner_thread_id||intent.dispatch_token!==chain.dispatch_token)throw new Error('Recovery requires the active serial owner and matching dispatch token');
 if(intent.character!==name||intent.direction!==direction||intent.revision!==revision||intent.max_requests!==1||!intent.reason)throw new Error('Invalid single-request recovery intent');
 if(intent.parent_request_sha256!==sha(parentRequest)||intent.parent_result_sha256!==sha(parentResult))throw new Error('Recovery parent fingerprint mismatch');
 recovery={mode:'explicit_http_failure_original_references',parent_request:parentRequest,parent_request_sha256:sha(parentRequest),parent_result:parentResult,parent_result_sha256:sha(parentResult),intent:intentFile,intent_sha256:sha(intentFile)};
}else if(revision)inputs.push(path.join(root,name,'generation',direction,'raw.png'));
for(const input of inputs)if(!fs.statSync(input).isFile())throw new Error('Input is not a file: '+input);
const prompt=fs.readFileSync(path.join(dir,'prompt.txt'),'utf8');
if(!prompt.trim())throw new Error('Empty image prompt');
const request={started:new Date().toISOString(),endpoint:'https://aihub.dog/v1/images/edits',model:'gpt-image-2',quality:'medium',n:1,size:'1536x1024',transport:curlTransport?'curl_https_no_retry':'node_fetch',...(verifiedDirectTransport?{direct_transport:'Explicit --noproxy * matching the inspected service control; no system proxy changes'}:{}),...(systemLocalProxy?{proxy_transport:{url:'http://127.0.0.1:7897',scope:'Explicit existing system local proxy; HTTPS CONNECT to the unchanged aihub.dog endpoint; certificate verification enabled'}}:{}),...(curlTransport?{resolve_transport:{hostname:'aihub.dog',ip:'191.101.132.254',scope:'Pinned good image-upstream edge per Docs/EnemyDirectionReview/Remaining_20261024/image_transport_edge_map_20261029_1830.md'}}:{}),inputs,input_sha256:inputs.map(sha),prompt,...(recovery?{recovery}:{}),...(artRevision?{art_revision:artRevision}:{})};
if(preflight){console.log(JSON.stringify({name,direction,revision,preflight:true,output,transport:request.transport,proxy_transport:request.proxy_transport,resolve_transport:request.resolve_transport,inputs,input_sha256:request.input_sha256,recovery,art_revision:artRevision}));process.exit(0);}
if(!process.env.AIHUB_IMAGE_API_KEY)throw new Error('Missing runtime AIHub credential');
const form=new FormData();
for(const [k,v] of Object.entries({model:request.model,quality:request.quality,n:'1',size:request.size,prompt}))form.set(k,v);
for(const input of inputs)form.append('image[]',new Blob([fs.readFileSync(input)],{type:'image/png'}),path.basename(input));
fs.writeFileSync(path.join(dir,'request.json'),JSON.stringify(request,null,2),{flag:'wx'});
try{
 let response,data;
 if(curlTransport){
  // Credential is supplied only through curl config stdin, never a process argument or disk file.
  const argv=['-q','--config','-','--silent','--show-error','--max-time','600','--proto','=https','--request','POST','--url',request.endpoint,'--write-out','\nCURL_HTTP_STATUS=%{http_code}\n'];
  if(systemLocalProxy){argv.push('--proxy','http://127.0.0.1:7897','--noproxy','');}
  else{
   if(verifiedDirectTransport)argv.push('--noproxy','*');
   argv.push('--resolve','aihub.dog:443:191.101.132.254');
  }
  for(const [k,v] of Object.entries({model:request.model,quality:request.quality,n:'1',size:request.size,prompt}))argv.push('--form-string',k+'='+v);
  for(const input of inputs)argv.push('--form','image[]=@"'+input.replaceAll('\\','/')+'";type=image/png');
  const childEnv={...process.env};delete childEnv.AIHUB_IMAGE_API_KEY;
  const result=spawnSync('curl.exe',argv,{input:'header = "Authorization: Bearer '+process.env.AIHUB_IMAGE_API_KEY+'"\n',encoding:'utf8',maxBuffer:32*1024*1024,timeout:610000,windowsHide:true,env:childEnv});
  if(recovery?.mode==='bounded_PossessedWarg_resume_preserving_unknown_original'){
   const match=result.stdout?.match(/\nCURL_HTTP_STATUS=(\d{3})\s*$/);
   fs.writeFileSync(path.join(dir,'transport_outcome.json'),JSON.stringify({observed_at:new Date().toISOString(),process_exit:result.status,error:result.error?{name:result.error.name,code:result.error.code,message:result.error.message}:null,http_status:match?Number(match[1]):null,stderr:result.stderr,automatic_retries:0,possible_charge:'not_independently_verified'},null,2),{flag:'wx'});
   if(result.stdout)fs.writeFileSync(path.join(dir,'provider_response.txt'),match?result.stdout.slice(0,match.index):result.stdout,{flag:'wx'});
  }
  if(result.error||result.status!==0)throw new Error('curl transport failed '+(result.status??result.error?.code)+' '+(result.stderr??'').slice(0,500));
  const match=result.stdout.match(/\nCURL_HTTP_STATUS=(\d{3})\s*$/);if(!match)throw new Error('curl returned no HTTP outcome');
  const status=Number(match[1]);response={status,ok:status>=200&&status<300};data=JSON.parse(result.stdout.slice(0,match.index));
 }else{
  response=await fetch(request.endpoint,{method:'POST',redirect:'error',signal:AbortSignal.timeout(600000),headers:{Authorization:`Bearer ${process.env.AIHUB_IMAGE_API_KEY}`},body:form});
  data=await response.json();
 }
 if(!response.ok){fs.writeFileSync(path.join(dir,'result.json'),JSON.stringify({finished:new Date().toISOString(),status:response.status,error:data.error},null,2));throw new Error('AIHub HTTP '+response.status+' '+(data.error?.code??''));}
 const item=data.data?.[0];
 if(item?.b64_json)fs.writeFileSync(output,Buffer.from(item.b64_json,'base64'));
 else if(item?.url){const result=await fetch(item.url,{redirect:'error'});if(!result.ok)throw new Error('Image download HTTP '+result.status);fs.writeFileSync(output,Buffer.from(await result.arrayBuffer()));}
 else throw new Error('Success response contained no image');
 fs.writeFileSync(path.join(dir,'result.json'),JSON.stringify({finished:new Date().toISOString(),status:response.status,usage:data.usage,bytes:fs.statSync(output).size},null,2));
 console.log(JSON.stringify({name,direction,status:response.status,file:output,bytes:fs.statSync(output).size}));
}catch(error){if(!fs.existsSync(path.join(dir,'result.json')))fs.writeFileSync(path.join(dir,'uncertain_result.json'),JSON.stringify({finished:new Date().toISOString(),error:error.name,message:error.message,note:'No automatic retry. Check for an existing server result before repeating.'},null,2));throw error;}
