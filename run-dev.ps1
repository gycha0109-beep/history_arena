param(
    [ValidateSet('preview','battle','test','record')]
    [string]$Mode = 'preview',
    [string]$GodotPath = ''
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

function Resolve-Godot {
    if ($GodotPath -and (Test-Path $GodotPath)) {
        return (Resolve-Path $GodotPath).Path
    }
    foreach ($exe in @('godot', 'godot.exe', 'Godot_v4.7.2-stable_win64.exe')) {
        $cmd = Get-Command $exe -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    }
    foreach ($candidate in @(
        (Join-Path $root '.tools\Godot_v4.7.2-stable_win64.exe'),
        (Join-Path $root 'Godot_v4.7.2-stable_win64.exe'),
        (Join-Path $env:USERPROFILE 'Downloads\Godot_v4.7.2-stable_win64.exe')
    )) {
        if (Test-Path $candidate) { return $candidate }
    }
    throw "Godot 실행 파일을 찾지 못했습니다. Godot 4.7.2 Standard를 설치하고 PATH에 등록하거나 -GodotPath로 위치를 지정하세요."
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
        @('--headless','--path',$root,'--script','res://tests/five_second_preview.gd')
    )
    foreach ($argsArray in $tests) {
        & $godot @argsArray
        if ($LASTEXITCODE -ne 0) { throw "Godot 자동 검사가 실패했습니다. 종료 코드: $LASTEXITCODE" }
    }
    Write-Host "모든 Godot 기본 검사 통과"
    exit 0
}

if ($Mode -eq 'record') {
    foreach ($required in @(
        'assets\characters\musashi\models\musashi.glb',
        'assets\characters\bruce_lee\models\bruce_lee.glb',
        'assets\weapons\katana.glb'
    )) {
        if (-not (Test-Path (Join-Path $root $required))) {
            throw "녹화를 중단했습니다. 필수 모델 파일이 없습니다: $required"
        }
    }
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
