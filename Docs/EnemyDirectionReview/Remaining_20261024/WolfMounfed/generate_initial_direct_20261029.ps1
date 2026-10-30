param([Parameter(Mandatory=$true)][ValidateSet('Up','Down')][string]$Direction,[ValidateSet('revision_01','revision_02')][string]$Revision)
$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot -Parent
$taskChain=Get-Content -LiteralPath (Join-Path $taskRoot 'conversation_chain.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($taskChain.state -ne 'active' -or $taskChain.owner_thread_id -ne $env:CODEX_THREAD_ID -or $taskChain.current_character -ne 'WolfMounfed' -or $taskChain.dispatch_token -ne 'wolfhound-to-wolfmounfed-20261029_222452-68c070b7-1479-493d-aae5-005029aba3d5') { throw 'Ownership mismatch' }
$taskBusy=@(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'node.exe' -and $_.CommandLine -match 'generate\.mjs' })
if ($taskBusy.Count -gt 0) { throw 'Generator process exists; inspect its outcome first' }
$taskDir=Join-Path $PSScriptRoot ('generation/'+$Direction)
if ($Revision) { $taskDir=Join-Path $taskDir $Revision }
foreach ($taskOutcome in @('request.json','raw.png','result.json','uncertain_result.json','console.txt')) {
    if (Test-Path -LiteralPath (Join-Path $taskDir $taskOutcome)) { throw ('Existing generation evidence: '+$taskOutcome) }
}
$taskEnvironmentNames=@('HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','NO_PROXY','AIHUB_IMAGE_API_KEY')
$taskEnvironmentBefore=@{}
foreach ($taskEnvName in $taskEnvironmentNames) { $taskEnvironmentBefore[$taskEnvName]=[Environment]::GetEnvironmentVariable($taskEnvName,'Process') }
try {
    foreach ($taskProxyName in @('HTTP_PROXY','HTTPS_PROXY','ALL_PROXY')) { [Environment]::SetEnvironmentVariable($taskProxyName,$null,'Process') }
    $env:NO_PROXY='aihub.dog'
    if ($Revision) {
        & (Join-Path $taskRoot 'generate_character.ps1') -Character WolfMounfed -Direction $Direction -Revision $Revision -AuthorizedNetworkRecovery -Transport Curl 2>&1 | Tee-Object -FilePath (Join-Path $taskDir 'console.txt')
    } else {
        & (Join-Path $taskRoot 'generate_character.ps1') -Character WolfMounfed -Direction $Direction -Transport Curl 2>&1 | Tee-Object -FilePath (Join-Path $taskDir 'console.txt')
    }
    if ($LASTEXITCODE -ne 0) { throw 'Generation failed; preserve actual outcome and do not repeat' }
} finally {
    foreach ($taskEnvName in $taskEnvironmentNames) { [Environment]::SetEnvironmentVariable($taskEnvName,$taskEnvironmentBefore[$taskEnvName],'Process') }
    $taskEnvironmentBefore=$null
}
