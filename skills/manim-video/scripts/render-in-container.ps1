# Render a manim-video job in the render container (the default render path).
# Thin shim for Windows PowerShell 5.1 and PowerShell 7: runs render_in_container.py
# (Python 3.9+, standard library only) with the same arguments, for example
#   & "$env:USERPROFILE\.agents\skills\manim-video\scripts\render-in-container.ps1" C:\jobs\demo --quality final
# Usage: render-in-container.ps1 --help
$passArgs = $args
$script = Join-Path $PSScriptRoot 'render_in_container.py'
foreach ($candidate in @(@('py', '-3'), @('python3'), @('python'))) {
    $cmd = Get-Command $candidate[0] -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $cmd) { continue }
    $pre = @($candidate | Select-Object -Skip 1)
    # The Microsoft Store "python" alias without Python installed fails this check (exit 9009).
    & $cmd.Source @pre -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' *> $null
    if ($LASTEXITCODE -eq 0) {
        & $cmd.Source @pre $script @passArgs
        exit $LASTEXITCODE
    }
}
[Console]::Error.WriteLine('render-in-container: needs Python 3.9 or newer (python.org installer, or: winget install Python.Python.3.12)')
exit 3
