param(
    [string]$Episode = "ep01"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

function Invoke-StageCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,

        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    Write-Host ""
    Write-Host "==> $Label" -ForegroundColor Cyan
    Write-Host "python -m feicai_seedance.cli $($Arguments -join ' ')" -ForegroundColor DarkGray

    & python -m feicai_seedance.cli @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: python -m feicai_seedance.cli $($Arguments -join ' ')"
    }
}

function Wait-ForDecision {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Stage
    )

    $assessmentPath = Join-Path $projectRoot "reports\assessments\$Episode\$Stage.md"
    $summaryPath = Join-Path $projectRoot "reports\reviews\$Episode\$Stage\summary.json"

    Write-Host ""
    Write-Host "Review for stage '$Stage' is ready." -ForegroundColor Yellow
    Write-Host "Assessment report: $assessmentPath"
    Write-Host "Review summary: $summaryPath"
    Write-Host ""
    Write-Host "Enter y to accept this stage and continue."
    Write-Host "Enter n to stop here and keep control in the terminal."

    while ($true) {
        $answer = (Read-Host "Continue with 'accept $Episode $Stage'? [y/n]").Trim().ToLowerInvariant()
        switch ($answer) {
            "y" { return $true }
            "n" { return $false }
            default {
                Write-Host "Please enter y or n." -ForegroundColor Red
            }
        }
    }
}

function Wait-OnFailure {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    Write-Host ""
    Write-Host $Message -ForegroundColor Red
    Read-Host "Press Enter to exit"
}

try {
    Invoke-StageCommand -Arguments @("status") -Label "Check current status"

    Invoke-StageCommand -Arguments @("start", $Episode) -Label "Stage 1: Director analysis"
    Invoke-StageCommand -Arguments @("review", $Episode, "director") -Label "Review director analysis"
    if (-not (Wait-ForDecision -Stage "director")) {
        Read-Host "Flow paused. Press Enter to exit"
        exit 0
    }

    Invoke-StageCommand -Arguments @("accept", $Episode, "director") -Label "Accept director analysis"
    Invoke-StageCommand -Arguments @("design", $Episode) -Label "Stage 2: Art design"
    Invoke-StageCommand -Arguments @("review", $Episode, "design") -Label "Review art design"
    if (-not (Wait-ForDecision -Stage "design")) {
        Read-Host "Flow paused. Press Enter to exit"
        exit 0
    }

    Invoke-StageCommand -Arguments @("accept", $Episode, "design") -Label "Accept art design"
    Invoke-StageCommand -Arguments @("prompt", $Episode) -Label "Stage 3: Storyboard prompts"
    Invoke-StageCommand -Arguments @("review", $Episode, "prompt") -Label "Review storyboard prompts"
    if (-not (Wait-ForDecision -Stage "prompt")) {
        Read-Host "Flow paused. Press Enter to exit"
        exit 0
    }

    Invoke-StageCommand -Arguments @("accept", $Episode, "prompt") -Label "Accept storyboard prompts"
    Invoke-StageCommand -Arguments @("status") -Label "Check final status"

    Write-Host ""
    Write-Host "Flow completed." -ForegroundColor Green
    Read-Host "Press Enter to exit"
}
catch {
    Wait-OnFailure -Message $_.Exception.Message
    exit 1
}
