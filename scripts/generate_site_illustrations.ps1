[CmdletBinding()]
param(
    [string[]]$Id,
    [ValidateSet('literary-gems', 'fun-rankings')]
    [string]$Group,
    [switch]$Force,
    [ValidateRange(60, 1800)]
    [int]$TimeoutSec = 300
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$manifestPath = Join-Path $PSScriptRoot 'illustration_manifest.json'
$generator = Join-Path $HOME '.copilot\skills\azure-gpt-image\scripts\generate-image.ps1'
$outputRoot = Join-Path $root 'assets\images\illustrations'

if (-not (Test-Path -LiteralPath $manifestPath)) {
    throw "Illustration manifest not found: $manifestPath"
}
if (-not (Test-Path -LiteralPath $generator)) {
    throw "Azure image generator not found: $generator"
}

$manifest = Get-Content -Raw -Encoding UTF8 -LiteralPath $manifestPath | ConvertFrom-Json
$items = @($manifest.items)
if ($Id) {
    $wanted = [System.Collections.Generic.HashSet[string]]::new([string[]]$Id)
    $items = @($items | Where-Object { $wanted.Contains($_.id) })
    $missing = @($Id | Where-Object { $_ -notin $items.id })
    if ($missing) { throw "Unknown illustration id(s): $($missing -join ', ')" }
}
if ($Group) {
    $items = @($items | Where-Object group -eq $Group)
}
if (-not $items) {
    throw 'No illustrations matched the requested filters.'
}

$style = @'
Create one premium 3:2 horizontal editorial illustration for a Chinese literary memoir website. Unified art direction: nostalgic cinematic realism, personal archive atmosphere, restrained painterly detail, subtle film grain, tactile surfaces, directional natural or localized light, nuanced low-saturation color with warm amber and muted blue-green accents. The image must feel like a specific remembered moment, not generic stock art. Anonymous Chinese people only when needed; avoid identifiable real faces. No visible words, letters, numbers, logos, watermarks, copyrighted characters, UI text, split-screen labels, borders, poster layout, gore, explicit injury, distorted hands or extra limbs. Keep one clear focal scene, professional magazine composition, strong depth, and enough quiet negative space.

Scene:
'@

$completed = 0
$skipped = 0
$failed = @()
foreach ($item in $items) {
    $directory = Join-Path $outputRoot $item.group
    $output = Join-Path $directory $item.filename
    if ((Test-Path -LiteralPath $output) -and -not $Force) {
        Write-Host "[$($completed + $skipped + 1)/$($items.Count)] skip $($item.id)"
        $skipped += 1
        continue
    }

    New-Item -ItemType Directory -Path $directory -Force | Out-Null
    Write-Host "[$($completed + $skipped + 1)/$($items.Count)] generate $($item.id)"
    try {
        & $generator `
            -Prompt ($style + $item.scene) `
            -OutputPath $output `
            -Size $manifest.size `
            -Quality $manifest.quality `
            -OutputFormat jpeg `
            -OutputCompression 88 `
            -TimeoutSec $TimeoutSec
        if ($LASTEXITCODE -ne 0) {
            throw "Image generator exited with code $LASTEXITCODE"
        }
        $completed += 1
    } catch {
        $failed += [pscustomobject]@{ id = $item.id; message = $_.Exception.Message }
        Write-Warning "$($item.id): $($_.Exception.Message)"
    }
}

$summary = [ordered]@{
    requested = $items.Count
    generated = $completed
    skipped = $skipped
    failed = $failed
}
$summary | ConvertTo-Json -Depth 5
if ($failed.Count) {
    throw "$($failed.Count) illustration(s) failed. Re-run the command to resume."
}
