<#
.SYNOPSIS
    Русификатор High Times — установщик.

.DESCRIPTION
    Копирует переведённые файлы localized.sq и vntext.sq в папку игры,
    предварительно сохранив оригиналы в подпапку backup рядом со
    скриптом. Также патчит закэшированную копию этих файлов в
    AppData\LocalLow\Yangyang Mobile\High Times, если она уже существует
    (иначе игра при следующем запуске всё равно подхватит английский
    текст из старого кэша вместо только что установленного перевода).

.PARAMETER GamePath
    Путь к папке с игрой (та, где лежит "High Times.exe").
    Если не указан, скрипт спросит его в интерактивном режиме.

.PARAMETER Uninstall
    Восстановить оригинальные (английские) файлы из бэкапа вместо установки.

.EXAMPLE
    .\install_russian.ps1 -GamePath "C:\Games\High Times"

.EXAMPLE
    .\install_russian.ps1 -GamePath "C:\Games\High Times" -Uninstall
#>

param(
    [string]$GamePath,
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PatchDir = Join-Path $ScriptDir "HighTimes_RU\High Times_Data\StreamingAssets\SqlText"
$BackupRoot = Join-Path $ScriptDir "backup"
$DbFiles = @("localized.sq", "vntext.sq")

function Get-CachePath {
    Join-Path $env:USERPROFILE "AppData\LocalLow\Yangyang Mobile\High Times"
}

function Confirm-GamePath([string]$path) {
    if (-not $path) {
        $path = Read-Host "Введите путь к папке с игрой (где лежит 'High Times.exe')"
    }
    $path = $path.Trim('"')
    $resolved = (Resolve-Path -LiteralPath $path -ErrorAction SilentlyContinue).Path
    if (-not $resolved) {
        Write-Host "[ОШИБКА] Путь не найден: $path" -ForegroundColor Red
        exit 1
    }
    $exe = Join-Path $resolved "High Times.exe"
    $sqltext = Join-Path $resolved "High Times_Data\StreamingAssets\SqlText"
    if (-not (Test-Path $exe) -or -not (Test-Path $sqltext)) {
        Write-Host "[ОШИБКА] По этому пути не похоже на установку High Times (нет 'High Times.exe' или 'High Times_Data\StreamingAssets\SqlText')." -ForegroundColor Red
        exit 1
    }
    return $resolved
}

function Do-Install([string]$gameDir) {
    $targetSqlText = Join-Path $gameDir "High Times_Data\StreamingAssets\SqlText"
    $cacheDir = Get-CachePath

    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupDir = Join-Path $BackupRoot "install_$stamp"
    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

    Write-Host "Папка игры: $gameDir"
    Write-Host ""
    Write-Host "ВНИМАНИЕ: файлы сохранений и кэш игры (AppData\LocalLow\Yangyang Mobile\High Times)" -ForegroundColor Yellow
    Write-Host "являются ОБЩИМИ для всех копий игры с таким названием на этом компьютере." -ForegroundColor Yellow
    Write-Host "Установка русификатора затронет и этот общий кэш." -ForegroundColor Yellow
    Write-Host ""
    $answer = Read-Host "Продолжить установку? [y/N]"
    if ($answer -notin @("y", "yes", "д", "да")) {
        Write-Host "Установка отменена."
        exit 0
    }

    foreach ($db in $DbFiles) {
        $patchFile = Join-Path $PatchDir $db
        if (-not (Test-Path $patchFile)) {
            Write-Host "[ОШИБКА] Не найден файл перевода: $patchFile" -ForegroundColor Red
            exit 1
        }

        # 1) бэкап + замена файла в папке игры
        $targetFile = Join-Path $targetSqlText $db
        if (Test-Path $targetFile) {
            $backupDest = Join-Path $backupDir "StreamingAssets_SqlText"
            New-Item -ItemType Directory -Force -Path $backupDest | Out-Null
            Copy-Item $targetFile (Join-Path $backupDest $db) -Force
        }
        Copy-Item $patchFile $targetFile -Force
        Write-Host "[*] Установлен: $targetFile"

        # 2) бэкап + замена закэшированной копии, если она уже есть
        if (Test-Path $cacheDir) {
            $cacheFile = Join-Path $cacheDir $db
            if (Test-Path $cacheFile) {
                $backupDest = Join-Path $backupDir "LocalLow_cache"
                New-Item -ItemType Directory -Force -Path $backupDest | Out-Null
                Copy-Item $cacheFile (Join-Path $backupDest $db) -Force
                Copy-Item $patchFile $cacheFile -Force
                Write-Host "[*] Обновлена кэш-копия: $cacheFile"
            }
        }
    }

    $manifest = @{
        timestamp = $stamp
        target    = $gameDir
    } | ConvertTo-Json
    Set-Content -Path (Join-Path $backupDir "manifest.json") -Value $manifest -Encoding UTF8

    Write-Host ""
    Write-Host "Готово! Русификатор установлен." -ForegroundColor Green
    Write-Host "Бэкап оригиналов: $backupDir"
    Write-Host "Для отката: .\install_russian.ps1 -GamePath `"$gameDir`" -Uninstall"
}

function Do-Uninstall([string]$gameDir) {
    if (-not (Test-Path $BackupRoot)) {
        Write-Host "[ОШИБКА] Папка с бэкапами не найдена: $BackupRoot" -ForegroundColor Red
        exit 1
    }
    $candidates = Get-ChildItem $BackupRoot -Directory -Filter "install_*" |
        Where-Object {
            $mf = Join-Path $_.FullName "manifest.json"
            if (Test-Path $mf) {
                $data = Get-Content $mf -Raw | ConvertFrom-Json
                $data.target -eq $gameDir
            } else { $false }
        } | Sort-Object Name -Descending

    if (-not $candidates) {
        Write-Host "[ОШИБКА] Не найден бэкап для этой папки игры: $gameDir" -ForegroundColor Red
        exit 1
    }
    $backupDir = $candidates[0].FullName
    Write-Host "Восстановление из: $backupDir"

    $answer = Read-Host "Восстановить оригинальные (английские) файлы? [y/N]"
    if ($answer -notin @("y", "yes", "д", "да")) {
        Write-Host "Отменено."
        exit 0
    }

    $targetSqlText = Join-Path $gameDir "High Times_Data\StreamingAssets\SqlText"
    $cacheDir = Get-CachePath

    $saBackupDir = Join-Path $backupDir "StreamingAssets_SqlText"
    if (Test-Path $saBackupDir) {
        foreach ($f in Get-ChildItem $saBackupDir -File) {
            Copy-Item $f.FullName (Join-Path $targetSqlText $f.Name) -Force
            Write-Host "[*] Восстановлен: $(Join-Path $targetSqlText $f.Name)"
        }
    }

    $llBackupDir = Join-Path $backupDir "LocalLow_cache"
    if ((Test-Path $llBackupDir) -and (Test-Path $cacheDir)) {
        foreach ($f in Get-ChildItem $llBackupDir -File) {
            Copy-Item $f.FullName (Join-Path $cacheDir $f.Name) -Force
            Write-Host "[*] Восстановлена кэш-копия: $(Join-Path $cacheDir $f.Name)"
        }
    }

    Write-Host ""
    Write-Host "Готово! Оригинальные файлы восстановлены." -ForegroundColor Green
}

$gameDir = Confirm-GamePath $GamePath

if ($Uninstall) {
    Do-Uninstall $gameDir
} else {
    Do-Install $gameDir
}
