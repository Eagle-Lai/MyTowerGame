$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot -Parent
$taskChain=Get-Content -LiteralPath (Join-Path $taskRoot 'conversation_chain.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($taskChain.state -ne 'active' -or $taskChain.owner_thread_id -ne $env:CODEX_THREAD_ID -or $taskChain.current_character -ne 'Zombie' -or $taskChain.dispatch_token -ne 'wolfmounfed-to-zombie-20261029_230534-9abf79b2-282d-4c43-bc85-2b10f14a62f1') { throw 'Ownership mismatch' }
$taskBusy=@(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'node.exe' -and $_.CommandLine -match 'generate\.mjs' })
if ($taskBusy.Count -gt 0) { throw 'Generator exists; inspect outcome' }
$taskDir=Join-Path $PSScriptRoot 'generation/Up/revision_01'
$taskIntent=Get-Content -Raw -Encoding UTF8 (Join-Path $taskDir 'art_correction_intent.json') | ConvertFrom-Json
if ($taskIntent.owner_thread_id -ne $env:CODEX_THREAD_ID -or $taskIntent.dispatch_token -ne $taskChain.dispatch_token -or $taskIntent.max_requests -ne 1) { throw 'Art correction intent mismatch' }
if ((Get-FileHash (Join-Path $PSScriptRoot 'generation/Up/raw.png')).Hash -ne $taskIntent.source_raw_sha256 -or (Get-FileHash (Join-Path $PSScriptRoot 'generation/Up/result.json')).Hash -ne $taskIntent.source_result_sha256) { throw 'Source success drift' }
foreach ($taskOutcome in @('request.json','raw.png','result.json','uncertain_result.json','console.txt')) { if (Test-Path (Join-Path $taskDir $taskOutcome)) { throw 'Outcome exists; refuse repeat' } }
$taskEnvironmentNames=@('HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','NO_PROXY','AIHUB_IMAGE_API_KEY')
$taskEnvironmentBefore=@{}
foreach ($taskEnvName in $taskEnvironmentNames) { $taskEnvironmentBefore[$taskEnvName]=[Environment]::GetEnvironmentVariable($taskEnvName,'Process') }
try {
 foreach ($taskProxyName in @('HTTP_PROXY','HTTPS_PROXY','ALL_PROXY')) { [Environment]::SetEnvironmentVariable($taskProxyName,$null,'Process') }
 $env:NO_PROXY='aihub.dog'
 & (Join-Path $taskRoot 'generate_character.ps1') -Character Zombie -Direction Up -Revision revision_01 -Transport Curl 2>&1 | Tee-Object -FilePath (Join-Path $taskDir 'console.txt')
 if ($LASTEXITCODE -ne 0) { throw 'Correction failed; preserve actual outcome, do not repeat' }
} finally {
 foreach ($taskEnvName in $taskEnvironmentNames) { [Environment]::SetEnvironmentVariable($taskEnvName,$taskEnvironmentBefore[$taskEnvName],'Process') }
 $taskEnvironmentBefore=$null
}
