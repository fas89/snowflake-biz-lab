#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$LocalReposDir,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$labRepo = (Resolve-Path (Join-Path $scriptDir '..')).ProviderPath
$launchpadFile = Join-Path $labRepo 'runtime\generated\launchpad.local.ps1'

if (-not $LocalReposDir) {
    $LocalReposDir = (Resolve-Path (Join-Path $labRepo '..')).ProviderPath
}
else {
    $LocalReposDir = (Resolve-Path $LocalReposDir).ProviderPath
}

# GitLab demo workspaces live INSIDE the lab repo at .\gitlab\ (gitignored).
# They are bootstrapped from fluid\fixtures\workspaces\ templates via
# `task workspaces:bootstrap`. The launchpad exports the expected subpaths
# so downstream helpers (reset_demo_state.py, docs snippets) resolve correctly.
$demoWorkspacesDir = Join-Path $labRepo 'gitlab'
$greenfieldWorkspace = Join-Path $demoWorkspacesDir 'path-a-telco-silver-product-demo'
$existingDbtWorkspace = Join-Path $demoWorkspacesDir 'path-b-ai-telco-silver-import-demo'
$greenfieldGitlabUrl = ''
$existingDbtGitlabUrl = ''
$fluidSecretsFile = Join-Path $labRepo 'runtime\generated\fluid.local.env'
$forgeCliRepo = Join-Path $LocalReposDir 'forge-cli'

function Quote-ForPowerShell {
    param([string]$Value)
    $escaped = $Value -replace '"', '""'
    return '"' + $escaped + '"'
}

New-Item -ItemType Directory -Force -Path (Join-Path $labRepo 'runtime\generated') | Out-Null

if ((Test-Path $launchpadFile) -and -not $Force) {
    Write-Host "Keeping existing launchpad file: $launchpadFile"
    Write-Host "This is normal if you already set up your local paths."
    Write-Host "Use -Force only when you want to regenerate it."
    Write-Host ''
    Write-Host 'Next step:'
    Write-Host '  . .\runtime\generated\launchpad.local.ps1'
    exit 0
}

$lines = @(
    "`$env:LOCAL_REPOS_DIR = $(Quote-ForPowerShell $LocalReposDir) # parent folder that holds snowflake-biz-lab and forge-cli",
    "`$env:LAB_REPO = $(Quote-ForPowerShell $labRepo) # local clone of this repo",
    "`$env:FORGE_CLI_REPO = $(Quote-ForPowerShell $forgeCliRepo) # editable forge-cli checkout or worktree",
    "`$env:DEMO_WORKSPACES_DIR = $(Quote-ForPowerShell $demoWorkspacesDir) # parent folder for the GitLab demo workspaces",
    "`$env:GREENFIELD_WORKSPACE = $(Quote-ForPowerShell $greenfieldWorkspace) # GitLab working copy for the main demo",
    "`$env:EXISTING_DBT_WORKSPACE = $(Quote-ForPowerShell $existingDbtWorkspace) # GitLab working copy for the existing-dbt variation",
    "`$env:GREENFIELD_GITLAB_URL = $(Quote-ForPowerShell $greenfieldGitlabUrl) # Git clone URL for the main demo workspace",
    "`$env:EXISTING_DBT_GITLAB_URL = $(Quote-ForPowerShell $existingDbtGitlabUrl) # Git clone URL for the existing-dbt demo workspace",
    "`$env:FLUID_SECRETS_FILE = $(Quote-ForPowerShell $fluidSecretsFile) # ignored file that holds Snowflake and DMM secrets"
)

Set-Content -Path $launchpadFile -Value $lines -Encoding UTF8

Write-Host "Created $launchpadFile"
Write-Host ''
Write-Host 'Detected values:'
Write-Host "  LOCAL_REPOS_DIR=$LocalReposDir"
Write-Host "  LAB_REPO=$labRepo"
Write-Host "  FORGE_CLI_REPO=$forgeCliRepo"
Write-Host "  DEMO_WORKSPACES_DIR=$demoWorkspacesDir"
Write-Host ''
Write-Host 'Next steps:'
Write-Host '  1. Review the generated file if you want to override any paths.'
Write-Host '  2. Load it into your shell to refresh the current path variables:'
Write-Host '     . .\runtime\generated\launchpad.local.ps1'
Write-Host '  3. Bootstrap the gitlab/ demo workspaces from tracked templates:'
Write-Host '     task workspaces:bootstrap'
Write-Host '  4. Continue with docs/launchpad-common.md'
