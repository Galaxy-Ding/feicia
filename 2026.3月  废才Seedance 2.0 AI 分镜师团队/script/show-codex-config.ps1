param(
    [string]$CodexConfigPath = "$env:USERPROFILE\.codex\config.toml",
    [string]$CodexAuthPath = "$env:USERPROFILE\.codex\auth.json"
)

if (-not (Test-Path -LiteralPath $CodexConfigPath)) {
    Write-Error "Codex config not found: $CodexConfigPath"
    exit 1
}

if (-not (Test-Path -LiteralPath $CodexAuthPath)) {
    Write-Error "Codex auth not found: $CodexAuthPath"
    exit 1
}

$configText = Get-Content -LiteralPath $CodexConfigPath -Raw -Encoding UTF8
$auth = Get-Content -LiteralPath $CodexAuthPath -Raw -Encoding UTF8 | ConvertFrom-Json

$baseUrlMatch = [regex]::Match($configText, "(?m)^\s*base_url\s*=\s*'([^']+)'")
$modelMatch = [regex]::Match($configText, "(?m)^\s*model\s*=\s*'([^']+)'")
$wireApiMatch = [regex]::Match($configText, "(?m)^\s*wire_api\s*=\s*'([^']+)'")
$providerNameMatch = [regex]::Match($configText, "(?m)^\s*name\s*=\s*'([^']+)'")

if (-not $baseUrlMatch.Success) {
    Write-Error "base_url is missing in $CodexConfigPath"
    exit 1
}

$apiKey = [string]$auth.OPENAI_API_KEY
if ([string]::IsNullOrWhiteSpace($apiKey)) {
    Write-Error "OPENAI_API_KEY is missing in $CodexAuthPath"
    exit 1
}

$baseUrl = $baseUrlMatch.Groups[1].Value.TrimEnd('/')
$model = if ($modelMatch.Success) { $modelMatch.Groups[1].Value } else { "<unknown>" }
$wireApi = if ($wireApiMatch.Success) { $wireApiMatch.Groups[1].Value } else { "responses" }
$providerName = if ($providerNameMatch.Success) { $providerNameMatch.Groups[1].Value } else { "custom" }
$maskedKey = if ($apiKey.Length -gt 8) {
    $apiKey.Substring(0, 4) + "***" + $apiKey.Substring($apiKey.Length - 4)
} else {
    "***"
}

Write-Output "Codex config file:"
Write-Output "  $CodexConfigPath"
Write-Output "Codex auth file:"
Write-Output "  $CodexAuthPath"
Write-Output ""
Write-Output "Detected values:"
Write-Output "  model            = $model"
Write-Output "  provider name    = $providerName"
Write-Output "  base_url         = $baseUrl"
Write-Output "  wire_api         = $wireApi"
Write-Output "  OPENAI_API_KEY   = $maskedKey"
Write-Output ""
Write-Output "Recommended project-config.json provider block for Codex:"
Write-Output "{"
Write-Output '  "provider": "openai-compatible",'
Write-Output "  `"base_url`": `"$baseUrl`","
Write-Output '  "api_key_env": "OPENAI_API_KEY",'
Write-Output '  "timeout_seconds": 300,'
Write-Output '  "max_retries": 3,'
Write-Output "  `"wire_api`": `"$wireApi`""
Write-Output "}"
Write-Output ""
Write-Output "Command to import Codex credentials into the current PowerShell session:"
Write-Output '$codex = Get-Content -LiteralPath "$env:USERPROFILE\.codex\auth.json" -Raw | ConvertFrom-Json'
Write-Output '$env:OPENAI_API_KEY = $codex.OPENAI_API_KEY'
