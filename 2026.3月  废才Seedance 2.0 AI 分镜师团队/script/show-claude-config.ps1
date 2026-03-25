param(
    [string]$ClaudeSettingsPath = "$env:USERPROFILE\.claude\settings.json"
)

if (-not (Test-Path -LiteralPath $ClaudeSettingsPath)) {
    Write-Error "Claude settings not found: $ClaudeSettingsPath"
    exit 1
}

$raw = Get-Content -LiteralPath $ClaudeSettingsPath -Raw -Encoding UTF8
$config = $raw | ConvertFrom-Json

if (-not $config.env) {
    Write-Error "No env object found in $ClaudeSettingsPath"
    exit 1
}

$authToken = [string]$config.env.ANTHROPIC_AUTH_TOKEN
$baseUrl = [string]$config.env.ANTHROPIC_BASE_URL

if ([string]::IsNullOrWhiteSpace($authToken)) {
    Write-Error "ANTHROPIC_AUTH_TOKEN is missing in $ClaudeSettingsPath"
    exit 1
}

if ([string]::IsNullOrWhiteSpace($baseUrl)) {
    Write-Error "ANTHROPIC_BASE_URL is missing in $ClaudeSettingsPath"
    exit 1
}

$trimmedBaseUrl = $baseUrl.TrimEnd('/')
$maskedToken = if ($authToken.Length -gt 8) {
    $authToken.Substring(0, 4) + "***" + $authToken.Substring($authToken.Length - 4)
} else {
    "***"
}

Write-Output "Claude settings file:"
Write-Output "  $ClaudeSettingsPath"
Write-Output ""
Write-Output "Detected values:"
Write-Output "  ANTHROPIC_BASE_URL   = $trimmedBaseUrl"
Write-Output "  ANTHROPIC_AUTH_TOKEN = $maskedToken"
Write-Output ""
Write-Output "Recommended project-config.json provider block for Claude:"
Write-Output "{"
Write-Output '  "provider": "openai-compatible",'
Write-Output "  `"base_url`": `"$trimmedBaseUrl/v1`","
Write-Output '  "api_key_env": "ANTHROPIC_AUTH_TOKEN",'
Write-Output '  "timeout_seconds": 300,'
Write-Output '  "max_retries": 3,'
Write-Output '  "wire_api": "responses"'
Write-Output "}"
Write-Output ""
Write-Output "Command to import Claude credentials into the current PowerShell session:"
Write-Output '$claude = Get-Content -LiteralPath "$env:USERPROFILE\.claude\settings.json" -Raw | ConvertFrom-Json'
Write-Output '$env:ANTHROPIC_AUTH_TOKEN = $claude.env.ANTHROPIC_AUTH_TOKEN'
