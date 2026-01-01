# Set error action preference to stop on any error
$ErrorActionPreference = "Stop"

# Create a log file with timestamp
$logFolder = Join-Path -Path $PSScriptRoot -ChildPath "logs"
if (-not (Test-Path $logFolder)) {
    New-Item -Path $logFolder -ItemType Directory | Out-Null
}
$logFile = Join-Path -Path $logFolder -ChildPath "deployment-safe-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

# Basic status message function
function Write-StatusMessage {
    param (
        [string]$Message,
        [ValidateSet("INFO", "SUCCESS", "WARNING", "ERROR")]
        [string]$Status = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Status) {
        "INFO" { "White" }
        "SUCCESS" { "Green" }
        "WARNING" { "Yellow" }
        "ERROR" { "Red" }
        default { "White" }
    }
    
    # Write to console with color
    Write-Host "[$timestamp] [$Status] $Message" -ForegroundColor $color
    
    # Also write to log file
    "[$timestamp] [$Status] $Message" | Out-File -FilePath $logFile -Append
}

Write-StatusMessage "Starting JuntoSummary deployment script (SAFE MODE)" -Status "INFO"
Write-StatusMessage "Log file created at: $logFile" -Status "INFO"

# Skip module checks in safe mode
Write-StatusMessage "Running in safe mode - skipping Azure module checks" -Status "INFO"

# Try to manually install Bicep via Azure CLI
Write-StatusMessage "Attempting to install Bicep using Azure CLI..." -Status "INFO"
try {
    & az version
    if ($LASTEXITCODE -eq 0) {
        Write-StatusMessage "Azure CLI is working. Installing Bicep extension..." -Status "INFO"
        & az extension add --name bicep --yes
        if ($LASTEXITCODE -eq 0) {
            Write-StatusMessage "Bicep extension installed successfully!" -Status "SUCCESS"
            
            # Try to install bicep binary
            Write-StatusMessage "Installing Bicep binary..." -Status "INFO"
            & az bicep install
            
            # Show where it's installed
            Write-StatusMessage "Bicep installation completed. Bicep should be available at:" -Status "SUCCESS"
            Write-StatusMessage "$env:USERPROFILE\.azure\bin\bicep.exe" -Status "INFO"
            Write-StatusMessage "Add this location to your PATH if needed." -Status "INFO"
        } else {
            Write-StatusMessage "Failed to install Bicep extension for Azure CLI" -Status "ERROR"
        }
    } else {
        Write-StatusMessage "Azure CLI is not working properly. Please check your installation." -Status "ERROR"
    }
} catch {
    Write-StatusMessage "Error: $_" -Status "ERROR"
}

Write-StatusMessage "Installation complete. Press Enter to exit..." -Status "INFO"
Read-Host