# Explicit opt-in: run in an elevated PowerShell. Blocks only this executable.
# Use a separate ToME installation for AP if ordinary ToME should stay online.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$GameExe,
    [Parameter(Mandatory=$true)][string]$Mailbox,
    [switch]$Remove
)
$ErrorActionPreference = 'Stop'
$exe = (Resolve-Path -LiteralPath $GameExe).Path
$bytes = [System.Text.Encoding]::UTF8.GetBytes($exe.ToLowerInvariant())
$hash = [System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)
$id = ([System.BitConverter]::ToString($hash)).Replace('-','').Substring(0,16)
$name = "ToMEArchipelago-Offline-$id"
if ($Remove) {
    Get-NetFirewallRule -Name $name -ErrorAction SilentlyContinue | Remove-NetFirewallRule
    Remove-Item -LiteralPath (Join-Path $Mailbox 'offline-policy.json') -ErrorAction SilentlyContinue
    Write-Host "Removed AP firewall rule for $exe"
    exit 0
}
if (-not (Get-NetFirewallRule -Name $name -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -Name $name -DisplayName "ToME AP offline ($id)" `
        -Direction Outbound -Program $exe -Action Block -Profile Any | Out-Null
}
$rule = Get-NetFirewallRule -Name $name
if ($rule.Enabled -ne 'True' -or $rule.Action -ne 'Block') {
    throw 'Firewall rule could not be verified.'
}
New-Item -ItemType Directory -Force -Path $Mailbox | Out-Null
$json = @{schema=1; mode='windows_firewall'; executable=$exe; rule=$name; confirmed=$true} | ConvertTo-Json
[System.IO.File]::WriteAllText((Join-Path $Mailbox 'offline-policy.json'), $json, (New-Object System.Text.UTF8Encoding $false))
Write-Host "ToME outbound networking is blocked for $exe. The Python AP bridge remains online."
Write-Host 'Also set Allow online events to Disabled in ToME, and use a new character.'
