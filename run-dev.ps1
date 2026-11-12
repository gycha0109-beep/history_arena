param(
    [ValidateSet('preview','battle','test','record','audit','batch','replay','dualqa')]
    [string]$Mode = 'preview',
    [string]$GodotPath = '',
    [ValidateRange(1,40)]
    [int]$Count = 12,
    [ValidateRange(0,2147483600)]
    [int]$FirstSeed = 20261112,
    [string]$ReplayFile = ''
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

function Resolve-Godot {
    if ($GodotPath -and (Test-Path $GodotPath)) {
        return (Resolve-Path $GodotPath).Path
    }
    if ($env:LEGENDARY_GODOT -and (Test-Path $env:LEGENDARY_GODOT)) { return $env:LEGENDARY_GODOT }
    foreach ($exe in @('godot', 'godot.exe', 'Godot_v4.7.2-stable_win64.exe')) {
        $cmd = Get-Command $exe -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    }
    foreach ($candidate in @(
        'D:\cha\.toolcache\godot\4.7.2\Godot_v4.7.2-stable_win64_console.exe',
        (Join-Path $root '.tools\Godot_v4.7.2-stable_win64.exe'),
        (Join-Path $root 'Godot_v4.7.2-stable_win64.exe'),
        (Join-Path $env:USERPROFILE 'Downloads\Godot_v4.7.2-stable_win64.exe')
    )) {
        if (Test-Path $candidate) { return $candidate }
    }
    throw "Godot 실행 파일을 찾지 못했습니다. Godot 4.7.2 Standard를 설치하고 PATH에 등록하거나 -GodotPath로 위치를 지정하세요."
}

function Invoke-AssetAudit {
    $checker = Join-Path $root 'tools\asset_audit.py'
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        & $python.Source $checker --root $root
    } else {
        $launcher = Get-Command py -ErrorAction SilentlyContinue
        if (-not $launcher) {
            throw "Python 설치를 찾지 못했습니다. 모델 검사에는 Python 3이 필요합니다."
        }
        & $launcher.Source -3 $checker --root $root
    }
    if ($LASTEXITCODE -ne 0) {
        throw "3D 모델·뼈·필수 모션·검 품질 검사가 실패했습니다. 위 오류를 수정하세요."
    }
}

if ($Mode -eq 'audit') {
    Invoke-AssetAudit
    Write-Host "모델·모션 구조 검사 통과"
    exit 0
}

$godot = Resolve-Godot
Write-Host "프로젝트: $root"
Write-Host "Godot: $godot"
Write-Host "작업: $Mode"

if ($Mode -eq 'test') {
    $tests = @(
        @('--headless','--editor','--path',$root,'--quit'),
        @('--headless','--path',$root,'--script','res://tests/smoke.gd'),
        @('--headless','--path',$root,'--script','res://tests/combat_simulation.gd'),
        @('--headless','--path',$root,'--script','res://tests/asset_pipeline.gd'),
        @('--headless','--path',$root,'--script','res://tests/five_second_preview.gd'),
        @('--headless','--path',$root,'--script','res://tests/replay_pipeline.gd'),
        @('--headless','--path',$root,'--script','res://tests/dual_wield_manifest.gd')
    )
    foreach ($argsArray in $tests) {
        & $godot @argsArray
        if ($LASTEXITCODE -ne 0) { throw "Godot 자동 검사가 실패했습니다. 종료 코드: $LASTEXITCODE" }
    }
    Write-Host "모든 Godot 기본 검사 통과"
    exit 0
}

if ($Mode -eq 'batch') {
    & $godot --headless --path $root --script res://tools/generate_matches.gd -- --count $Count --first-seed $FirstSeed --out-dir res://captures/matches
    if ($LASTEXITCODE -ne 0) { throw "경기 자동 생성·저장에 실패했습니다." }
    Write-Host "경기 목록: $root\captures\matches\index.json"
    exit 0
}

if ($Mode -eq 'replay') {
    $replayArg = $ReplayFile
    if (-not $replayArg) {
        $indexFile = Join-Path $root 'captures\matches\index.json'
        if (-not (Test-Path $indexFile)) {
            throw "저장된 경기 목록이 없습니다. 먼저 run-dev.cmd -Mode batch를 실행하세요."
        }
        $selection = Get-Content -LiteralPath $indexFile -Raw -Encoding UTF8 | ConvertFrom-Json
        if (-not $selection.selected_file) { throw "저장된 경기 목록에 추천 경기가 없습니다." }
        $replayArg = "res://captures/matches/" + $selection.selected_file
    }
    & $godot --path $root res://scenes/replay_viewer.tscn -- --replay $replayArg
    if ($LASTEXITCODE -ne 0) { throw "저장된 경기 재생을 시작하지 못했습니다." }
    exit 0
}


if ($Mode -eq 'dualqa') {
    foreach ($sample in @(
        'samples\external\CesiumMan.glb',
        'samples\external\qa_katana_dual.glb',
        'samples\external\qa_wakizashi_dual.glb'
    )) {
        if (-not (Test-Path (Join-Path $root $sample))) {
            throw "??? ??? ??? ????: $sample. ?? docs/DUAL_WIELD_QA.md? ?????."
        }
    }
    $captureDir = Join-Path $root 'captures\qa'
    New-Item -ItemType Directory -Path $captureDir -Force | Out-Null
    & $godot --headless --editor --path $root --quit
    if ($LASTEXITCODE -ne 0) { throw "Godot ?? ????? ??????." }
    $avi = Join-Path $captureDir 'dual_wield_final.avi'
    $mp4 = Join-Path $captureDir 'dual_wield_final.mp4'
    & $godot --path $root --fixed-fps 60 --write-movie $avi --quit-after 300 res://scenes/qa_rigged_sample.tscn
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $avi)) {
        throw "??? 5? ?? ??? ??????."
    }
    $encoder = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if (-not $encoder) { throw "AVI? ????? FFmpeg? ?? ?????: $avi" }
    & $encoder.Source -hide_banner -loglevel error -y -i $avi -c:v libx264 -crf 19 -pix_fmt yuv420p -movflags +faststart $mp4
    if ($LASTEXITCODE -ne 0) { throw "MP4 ??? ??????." }
    & $encoder.Source -hide_banner -loglevel error -y -ss 2.0 -i $mp4 -frames:v 1 (Join-Path $captureDir 'dual_wield_poster.png')
    if ($LASTEXITCODE -ne 0) { throw "HTML ??? ??? ??? ??????." }
    Copy-Item -LiteralPath (Join-Path $root 'tools\dual_qa_viewer.html') -Destination (Join-Path $captureDir 'dual_wield_preview.html') -Force
    Write-Host "??? ??: $mp4"
    Write-Host ("HTML ????: " + (Join-Path $captureDir 'dual_wield_preview.html'))
    exit 0
}

if ($Mode -eq 'record') {
    Invoke-AssetAudit
    foreach ($required in @(
        'assets\characters\musashi\models\musashi.glb',
        'assets\characters\bruce_lee\models\bruce_lee.glb',
        'assets\weapons\katana.glb',
        'assets\weapons\wakizashi.glb'
    )) {
        if (-not (Test-Path (Join-Path $root $required))) {
            throw "녹화를 중단했습니다. 필수 모델 파일이 없습니다: $required"
        }
    }
    & $godot --headless --editor --path $root --quit
    if ($LASTEXITCODE -ne 0) { throw "Godot가 GLB 에셋을 읽어들이지 못했습니다." }
    & $godot --headless --path $root --script res://tests/asset_readiness.gd
    if ($LASTEXITCODE -ne 0) { throw "캐릭터 리깅, 모션, 손뼈 또는 검 연결이 불완전하여 녹화를 중단했습니다." }
    $captures = Join-Path $root 'captures'
    New-Item -ItemType Directory -Path $captures -Force | Out-Null
    $avi = Join-Path $captures 'preview_5s.avi'
    $mp4 = Join-Path $captures 'preview_5s.mp4'
    & $godot --path $root --resolution 720x1280 --write-movie $avi --fixed-fps 60 --quit-after 300 res://scenes/preview_five_seconds.tscn
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $avi)) {
        throw "Godot 장면 녹화가 완료되지 않았습니다."
    }
    $ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if ($ffmpeg) {
        & $ffmpeg.Source -y -i $avi -c:v libx264 -crf 18 -pix_fmt yuv420p -r 60 -movflags +faststart $mp4
        if ($LASTEXITCODE -ne 0) { throw "AVI는 생성됐지만 MP4 변환에 실패했습니다: $avi" }
        Write-Host "영상 생성: $mp4"
    } else {
        Write-Host "FFmpeg가 없어 AVI만 생성했습니다: $avi"
    }
    exit 0
}

if ($Mode -eq 'battle') {
    & $godot --path $root
} else {
    & $godot --path $root res://scenes/preview_five_seconds.tscn
}
if ($LASTEXITCODE -ne 0) { throw "Godot 실행 실패: 종료 코드 $LASTEXITCODE" }
