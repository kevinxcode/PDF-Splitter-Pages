param(
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
$uvCachePath = Join-Path $projectRoot ".uv-cache"

Set-Location $projectRoot
$env:UV_CACHE_DIR = $uvCachePath

if (-not (Test-Path -LiteralPath $pythonPath)) {
    $uvCommand = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $uvCommand) {
        throw "Python environment belum tersedia. Instal uv dari https://docs.astral.sh/uv/ lalu jalankan ulang."
    }
    uv venv .venv --python 3.11
}

$uvCommand = Get-Command uv -ErrorAction SilentlyContinue
if ($uvCommand) {
    uv pip install --python $pythonPath -r requirements-dev.txt
} else {
    & $pythonPath -m pip install -r requirements-dev.txt
}

# Some restricted Windows environments can execute Python outside the project
# but prevent Tcl from loading its script library there. Copying the library
# into the build workspace gives PyInstaller a reliable, readable source.
$savedErrorAction = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $pythonPath -c "import tkinter; tkinter.Tcl()" 2>$null
$tclProbeExitCode = $LASTEXITCODE
$ErrorActionPreference = $savedErrorAction
if ($tclProbeExitCode -ne 0) {
    $pythonBase = & $pythonPath -c "import sys; print(sys.base_prefix)"
    $tclSource = Join-Path $pythonBase "tcl"
    $tclBuildRoot = Join-Path $projectRoot ".build-tcl"
    $tclLibrary = Join-Path $tclBuildRoot "tcl8.6"
    $tkLibrary = Join-Path $tclBuildRoot "tk8.6"
    if (-not (Test-Path -LiteralPath (Join-Path $tclSource "tcl8.6\init.tcl"))) {
        throw "Instalasi Python tidak memiliki runtime Tcl/Tk yang lengkap."
    }
    New-Item -ItemType Directory -Force -Path $tclBuildRoot | Out-Null
    Copy-Item -LiteralPath (Join-Path $tclSource "tcl8.6") -Destination $tclBuildRoot -Recurse -Force
    Copy-Item -LiteralPath (Join-Path $tclSource "tk8.6") -Destination $tclBuildRoot -Recurse -Force
    $env:TCL_LIBRARY = $tclLibrary
    $env:TK_LIBRARY = $tkLibrary
}

if (-not $SkipTests) {
    & $pythonPath -m pytest -q
    if ($LASTEXITCODE -ne 0) {
        throw "Pengujian gagal; build dibatalkan."
    }
}

& $pythonPath -m PyInstaller --noconfirm --clean PDFSplitter.spec
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller gagal membuat aplikasi."
}

$outputPath = Join-Path $projectRoot "dist\PDFSplitter.exe"
if (-not (Test-Path -LiteralPath $outputPath)) {
    throw "Build selesai tanpa menghasilkan PDFSplitter.exe."
}

Write-Host "Build berhasil: $outputPath" -ForegroundColor Green

