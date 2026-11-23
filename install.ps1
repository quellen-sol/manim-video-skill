# Make the manim-video skill discoverable by agents (Windows PowerShell 5.1 or PowerShell 7).
# Thin shim: runs install.py (Python 3.9+, standard library only) with the same options, e.g.
#   .\install.ps1              link into %USERPROFILE%\.agents\skills and %USERPROFILE%\.claude\skills
#   .\install.ps1 --dry-run    show what it would do;  .\install.ps1 --help  all options
# Links are symlinks when allowed (Developer Mode or an elevated shell), otherwise directory
# junctions, otherwise marked copies.
$passArgs = $args
$script = Join-Path $PSScriptRoot 'install.py'
foreach ($candidate in @(@('py', '-3'), @('python3'), @('python'))) {
    $cmd = Get-Command $candidate[0] -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $cmd) { continue }
    $pre = @($candidate | Select-Object -Skip 1)
    & $cmd.Source @pre -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' *> $null
    if ($LASTEXITCODE -eq 0) {
        & $cmd.Source @pre $script @passArgs
        exit $LASTEXITCODE
    }
}
[Console]::Error.WriteLine('install.ps1: needs Python 3.9 or newer (python.org installer, or: winget install Python.Python.3.12)')
exit 1
