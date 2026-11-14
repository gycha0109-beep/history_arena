# Blender Studio CC0 Human Base Meshes 1.4.1 - local cache bootstrap
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$target = Join-Path $root 'assets\source_candidates\blender_human_base_meshes'
$blend = Join-Path $target 'human-base-meshes-bundle-v1.4.1\human_base_meshes_bundle.blend'
if (Test-Path $blend) { Write-Host 'CC0 anatomy source already present'; exit 0 }
New-Item -ItemType Directory -Force -Path $target | Out-Null
$url = 'https://download.blender.org/demo/asset-bundles/human-base-meshes/human-base-meshes-bundle-v1.4.1.zip'
$archive = Join-Path $target 'human-base-meshes-bundle-v1.4.1.zip'
& curl.exe --fail -L --retry 3 --retry-delay 2 --output $archive $url
if ($LASTEXITCODE -ne 0) { throw "Download failed: $LASTEXITCODE" }
if ((Get-Item $archive).Length -ne 50643039) { throw 'CC0 archive byte size mismatch' }
& tar.exe -xf $archive -C $target
if ($LASTEXITCODE -ne 0 -or !(Test-Path $blend)) { throw 'CC0 anatomy extract failed' }
Write-Host 'CC0 anatomy source installed'
