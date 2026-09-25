[CmdletBinding()]
param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$resolvedRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$directories = @(
    'api', 'api_app', 'api_models', 'solver_core',
    'app', 'app/learn', 'app/solve',
    'components/shell', 'components/solver', 'components/results',
    'components/math', 'components/ui',
    'lib/api', 'lib/contracts', 'scripts',
    'tests/python', 'tests/frontend', 'tests/e2e',
    'public', 'docs', '.github/workflows'
)

foreach ($directory in $directories) {
    New-Item -ItemType Directory -Path (Join-Path $resolvedRoot $directory) -Force | Out-Null
}

Write-Output "Folder structure ready at $resolvedRoot"
