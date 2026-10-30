param([Parameter(Mandatory=$true)][string]$Character,[ValidateSet('Up','Down')][string]$Direction,[string]$Revision,[switch]$RecoverFailed,[switch]$AuthorizedUncertainRetry,[switch]$AuthorizedNetworkRecovery,[switch]$AuthorizedResume,[string]$ArtSourceRevision,[ValidateSet('Curl','Node')][string]$Transport='Curl',[switch]$UseSystemLocalProxy,[switch]$Preflight)
$ErrorActionPreference='Stop'
$taskImageArgs=@((Join-Path $PSScriptRoot 'generate.mjs'),$Character,$Direction)
if ($Revision) { $taskImageArgs+=$Revision }
if ($Transport -eq 'Curl') { $taskImageArgs+='--curl-transport' }
if ($UseSystemLocalProxy) {
    if ($Transport -ne 'Curl') { throw 'System local proxy is supported only by the explicit Curl transport' }
    $taskImageArgs+='--system-local-proxy'
}
if ($AuthorizedResume) {
    if ($RecoverFailed -or $AuthorizedUncertainRetry -or $AuthorizedNetworkRecovery -or $ArtSourceRevision -or -not $Revision) { throw 'Resume requires its own fresh revision and exactly one mode' }
    $taskActiveGenerators=@(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'node.exe' -and $_.CommandLine -match 'generate\.mjs' })
    if ($taskActiveGenerators.Count -gt 0) { throw 'A generator is still running; inspect before resume' }
    $taskImageArgs+='--authorized-resume'
}
if ($ArtSourceRevision) {
    if ($RecoverFailed -or $AuthorizedUncertainRetry -or $AuthorizedNetworkRecovery -or -not $Revision) { throw 'Art correction requires a fresh revision and exactly one mode' }
    $taskActiveGenerators=@(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'node.exe' -and $_.CommandLine -match 'generate\.mjs' })
    if ($taskActiveGenerators.Count -gt 0) { throw 'A generator is still running; inspect before art correction' }
    $taskImageArgs+=('--art-source='+$ArtSourceRevision)
}
if ($AuthorizedNetworkRecovery) {
    if ($RecoverFailed -or $AuthorizedUncertainRetry -or -not $Revision) { throw 'Choose exactly one recovery mode and a fresh revision' }
    $taskActiveGenerators=@(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'node.exe' -and $_.CommandLine -match 'generate\.mjs' })
    if ($taskActiveGenerators.Count -gt 0) { throw 'A generator is still running; inspect before recovery' }
    $taskImageArgs+='--authorized-network-recovery'
}
if ($AuthorizedUncertainRetry) {
    if ($RecoverFailed) { throw 'Choose exactly one recovery mode' }
    if ($Character -ne 'SabretoothTiger' -or $Direction -ne 'Down' -or $Revision -ne 'revision_02') { throw 'Authorization covers only SabretoothTiger Down revision_02' }
    $taskActiveGenerators=@(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'node.exe' -and $_.CommandLine -match 'generate\.mjs' })
    if ($taskActiveGenerators.Count -gt 0) { throw 'An image generator is still running; inspect its outcome first' }
    $taskImageArgs+='--authorized-uncertain-retry'
}
if ($RecoverFailed) {
    if (-not $Revision) { throw 'Failed-request recovery requires a fresh revision' }
    $taskActiveGenerators=@(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'node.exe' -and $_.CommandLine -match 'generate\.mjs' })
    if ($taskActiveGenerators.Count -gt 0) { throw 'An image generator is still running; inspect its outcome before recovery' }
    $taskImageArgs+='--recover-failed'
}
if ($Preflight) {
    $taskImageArgs+='--preflight'
    & node @taskImageArgs
    if ($LASTEXITCODE -ne 0) { throw ('Image preflight failed for '+$Character+' '+$Direction) }
    return
}
$taskImageSecure=Import-Clixml -LiteralPath 'C:/Users/Administrator/.codex/secrets/aihub-image-key.clixml'
try {
    $env:AIHUB_IMAGE_API_KEY=[System.Management.Automation.PSCredential]::new('image',$taskImageSecure).GetNetworkCredential().Password
    & node @taskImageArgs
    if ($LASTEXITCODE -ne 0) { throw ('Image request failed for '+$Character+' '+$Direction) }
} finally {
    Remove-Item Env:AIHUB_IMAGE_API_KEY -ErrorAction SilentlyContinue
    $taskImageSecure=$null
}
