# Monthly MOU Email Script for Windows
# This script activates the virtual environment and runs the Django management command

# Configuration
$ProjectDir = "C:\path\to\your\project"
$VenvDir = "$ProjectDir\venv"
$LogFile = "$ProjectDir\logs\mou_emails.log"

# Ensure log directory exists
$LogDir = Split-Path -Parent $LogFile
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# Change to project directory
Set-Location -Path $ProjectDir

# Log start
$StartTime = Get-Date
Add-Content -Path $LogFile -Value "----------------------------------------"
Add-Content -Path $LogFile -Value "Started at: $StartTime"

try {
    # Activate virtual environment and run command
    & "$VenvDir\Scripts\Activate.ps1"
    & "$VenvDir\Scripts\python.exe" manage.py send_monthly_mou_emails 2>&1 | Tee-Object -Append -FilePath $LogFile
    $ExitCode = $LASTEXITCODE
}
catch {
    $ErrorMsg = $_.Exception.Message
    Add-Content -Path $LogFile -Value "ERROR: $ErrorMsg"
    $ExitCode = 1
}
finally {
    # Deactivate virtual environment
    if (Get-Command deactivate -ErrorAction SilentlyContinue) {
        deactivate
    }
}

# Log finish
$EndTime = Get-Date
$Duration = $EndTime - $StartTime
Add-Content -Path $LogFile -Value "Finished at: $EndTime"
Add-Content -Path $LogFile -Value "Duration: $Duration"
Add-Content -Path $LogFile -Value "Exit code: $ExitCode"

exit $ExitCode
