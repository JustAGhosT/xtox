<#
.SYNOPSIS
    Deploys JuntoSummary infrastructure to Azure using Bicep templates
.DESCRIPTION
    This script provides a menu-driven interface to deploy Azure resources for the JuntoSummary project
    with proper error handling and display
.EXAMPLE
    .\deploy-infrastructure.ps1
#>

# Set error action preference to stop on any error
$ErrorActionPreference = "Stop"

# Create a log file with timestamp
$logFolder = Join-Path -Path $PSScriptRoot -ChildPath "logs"
if (-not (Test-Path $logFolder)) {
    New-Item -Path $logFolder -ItemType Directory | Out-Null
}
$logFile = Join-Path -Path $logFolder -ChildPath "deployment-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"
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

function Confirm-AzModules {
    try {
        # Check if Az modules are installed
        if (-not (Get-Module -ListAvailable -Name Az)) {
            Write-StatusMessage "Azure PowerShell modules not found. Installing..." -Status "WARNING"
            Install-Module -Name Az -Scope CurrentUser -Repository PSGallery -Force
        }
        
        # Import Az module if not already imported
        if (-not (Get-Module -Name Az)) {
            Import-Module Az -ErrorAction Stop
        }
        return $true
    }
    catch {
        Write-StatusMessage "Failed to load Azure PowerShell modules: $_" -Status "ERROR"
        Write-StatusMessage "Please run: Install-Module -Name Az -Scope CurrentUser -Repository PSGallery -Force" -Status "INFO"
        return $false
    }
}

function Confirm-BicepInstalled {
    try {
        # Check additional Bicep locations first (including Azure CLI's installation path)
        $commonPaths = @(
            # Azure CLI paths
            "$env:USERPROFILE\.azure\bin",           # Primary Azure CLI bicep location
            "$env:LOCALAPPDATA\.azure\bin",          # Alternative Azure CLI location
            
            # Standard MSI/installer paths
            "$env:ProgramFiles\Microsoft Bicep CLI",
            "C:\ProgramData\chocolatey\lib\bicep\tools",
            
            # Default paths already in script
            "$env:ProgramFiles\Bicep",
            "$env:ProgramFiles\Azure\Bicep",
            "$env:LocalAppData\Programs\Bicep"
        )
        
        # Check if Bicep exists in any of the common paths
        foreach ($path in $commonPaths) {
            $bicepExePath = Join-Path -Path $path -ChildPath "bicep.exe"
            if (Test-Path $bicepExePath) {
                Write-StatusMessage "Bicep CLI found at: $bicepExePath" -Status "SUCCESS"
                
                # Add to PATH temporarily if not already in PATH
                $envPaths = $env:PATH -split ';'
                $pathInEnv = $envPaths | Where-Object { $_.TrimEnd('\') -ieq $path.TrimEnd('\') }
                if (-not $pathInEnv) {
                    Write-StatusMessage "Adding Bicep location to PATH for this session..." -Status "INFO"
                    $env:PATH = "$path;$env:PATH"
                }
                
                # Try to get the version now that it's in PATH
                $version = & bicep --version 2>$null
                if ($version) {
                    Write-StatusMessage "Bicep version: $version" -Status "INFO"
                }
                
                return $true
            }
        }
        
        # If no direct executable found, check if bicep is available in PATH
        $bicepPath = Get-Command bicep -ErrorAction SilentlyContinue
        if ($bicepPath) {
            Write-StatusMessage "Bicep CLI found at: $($bicepPath.Source)" -Status "SUCCESS"
            $version = & bicep --version
            Write-StatusMessage "Bicep version: $version" -Status "INFO"
            return $true
        }
        
        # If not found, check for Azure CLI with Bicep extension
        $azPath = Get-Command az -ErrorAction SilentlyContinue
        if ($azPath) {
            Write-StatusMessage "Azure CLI found, checking for Bicep extension..." -Status "INFO"
            
            # First check using az bicep version (available if installed)
            $bicepVersion = & az bicep version 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-StatusMessage "Bicep installed via Azure CLI: $bicepVersion" -Status "SUCCESS"
                
                # Try to locate the actual executable path
                $azBicepPath = & az bicep install --query "bicepPath" -o tsv 2>$null
                if ($azBicepPath) {
                    Write-StatusMessage "Bicep executable path: $azBicepPath" -Status "INFO"
                    
                    # Add to PATH temporarily
                    $bicepDir = Split-Path -Parent $azBicepPath
                    Write-StatusMessage "Adding $bicepDir to PATH for this session..." -Status "INFO"
                    $env:PATH = "$bicepDir;$env:PATH"
                }
                
                return $true
            }
            
            # Fall back to extension list if version command fails
            $bicepExtension = & az extension list --query "[?name=='bicep'].version" -o tsv
            if ($bicepExtension) {
                Write-StatusMessage "Bicep extension for Azure CLI found (version $bicepExtension)" -Status "SUCCESS"
                
                # Try to install/upgrade and get the path
                Write-StatusMessage "Ensuring Bicep CLI is available in PATH..." -Status "INFO"
                & az bicep install --upgrade 2>$null
                
                return $true
            }
        }
        
        # Bicep not found, try to install it
        Write-StatusMessage "Bicep CLI not found. Attempting to install..." -Status "WARNING"
        
        # Check OS platform
        if ($IsWindows -or (!$IsLinux -and !$IsMacOS)) {
            # Windows installation - try Azure CLI first as it's most reliable
            if ($azPath) {
                Write-StatusMessage "Installing Bicep using Azure CLI..." -Status "INFO"
                & az bicep install
                if ($LASTEXITCODE -eq 0) {
                    Write-StatusMessage "Bicep installed successfully via Azure CLI" -Status "SUCCESS"
                    return $true
                }
            }
            
            # Fall back to Windows installer
            Write-StatusMessage "Installing Bicep for Windows..." -Status "INFO"
            
            # Create a temp directory
            $tempDir = Join-Path -Path $env:TEMP -ChildPath "BicepInstall"
            if (Test-Path $tempDir) { Remove-Item -Path $tempDir -Recurse -Force }
            New-Item -Path $tempDir -ItemType Directory | Out-Null
            
            # Download installer
            $installerUrl = "https://github.com/Azure/bicep/releases/latest/download/bicep-setup-win-x64.exe"
            $installerPath = Join-Path -Path $tempDir -ChildPath "bicep-setup-win-x64.exe"
            
            Write-StatusMessage "Downloading Bicep installer..." -Status "INFO"
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath
            
            # Run installer
            Write-StatusMessage "Running Bicep installer..." -Status "INFO"
            Start-Process -FilePath $installerPath -ArgumentList "/VERYSILENT /SUPPRESSMSGBOXES" -Wait
            
            # Check if installed successfully
            $bicepPath = Get-Command bicep -ErrorAction SilentlyContinue
            if ($bicepPath) {
                Write-StatusMessage "Bicep installed successfully" -Status "SUCCESS"
                return $true
            }
            else {
                Write-StatusMessage "Automatic Bicep installation failed" -Status "ERROR"
                Write-StatusMessage "Please install Bicep manually from https://aka.ms/bicep-install" -Status "INFO"
                return $false
            }
        }
        elseif ($IsLinux) {
            # Linux installation
            Write-StatusMessage "Installing Bicep for Linux..." -Status "INFO"
            Write-StatusMessage "Please run the following commands in your terminal:" -Status "INFO"
            Write-StatusMessage "curl -Lo bicep https://github.com/Azure/bicep/releases/latest/download/bicep-linux-x64" -Status "INFO"
            Write-StatusMessage "chmod +x ./bicep" -Status "INFO"
            Write-StatusMessage "sudo mv ./bicep /usr/local/bin/bicep" -Status "INFO"
            return $false
        }
        elseif ($IsMacOS) {
            # macOS installation
            Write-StatusMessage "Installing Bicep for macOS..." -Status "INFO"
            Write-StatusMessage "Please run the following command in your terminal:" -Status "INFO"
            Write-StatusMessage "brew install azure/bicep/bicep" -Status "INFO"
            return $false
        }
        
        return $false
    }
    catch {
        Write-StatusMessage "Error checking for Bicep: $_" -Status "ERROR"
        return $false
    }
}
function Connect-ToAzure {
    try {
        $context = Get-AzContext -ErrorAction SilentlyContinue
        if (-not $context) {
            Write-StatusMessage "Not connected to Azure. Initiating login..." -Status "INFO"
            Connect-AzAccount -ErrorAction Stop
            $context = Get-AzContext
            if (-not $context) {
                throw "Failed to connect to Azure after login attempt"
            }
        }
        Write-StatusMessage "Connected to Azure as: $($context.Account.Id)" -Status "SUCCESS"
        Write-StatusMessage "Subscription: $($context.Subscription.Name) ($($context.Subscription.Id))" -Status "INFO"
        return $true
    }
    catch {
        Write-StatusMessage "Failed to connect to Azure: $_" -Status "ERROR"
        return $false
    }
}

function Deploy-Bicep {
    param (
        [Parameter(Mandatory = $true)]
        [ValidateSet("dev", "test", "prod")]
        [string]$Environment,
        
        [Parameter(Mandatory = $false)]
        [string]$Location = "westeurope",
        
        [Parameter(Mandatory = $false)]
        [string]$ResourceGroupName = ""
    )
    
    try {
        # First check if Bicep is installed
        $bicepInstalled = Confirm-BicepInstalled
        if (-not $bicepInstalled) {
            Write-StatusMessage "Cannot detect Bicep CLI through standard checks." -Status "WARNING"
            
            # Give user option to continue anyway
            $continueAnyway = Read-Host "Do you want to continue with deployment anyway? (y/N)"
            if ($continueAnyway -ne "y" -and $continueAnyway -ne "Y") {
                Write-StatusMessage "Deployment canceled. Please install Bicep first." -Status "INFO"
                return $false
            }
            
            Write-StatusMessage "Continuing deployment despite Bicep detection failure..." -Status "WARNING"
            Write-StatusMessage "This may work if Bicep is installed but not detected properly." -Status "INFO"
            
            # Let's try one more attempt to use Azure CLI's bicep if available
            try {
                Write-StatusMessage "Attempting to install/use Azure CLI's Bicep extension as a last resort..." -Status "INFO"
                & az bicep install --force 2>&1 | Out-Null
            }
            catch {
                Write-StatusMessage "Failed to use Azure CLI's Bicep, proceeding anyway..." -Status "WARNING"
            }
        }

        $startTime = Get-Date
        $shortLocation = "we" # Short form of westeurope
        
        # Set default resource group name if not provided
        if ([string]::IsNullOrEmpty($ResourceGroupName)) {
            $ResourceGroupName = "$Environment-$shortLocation-rg-juntosummary"
        }
        
        # Create or check resource group
        $resourceGroup = Get-AzResourceGroup -Name $ResourceGroupName -ErrorAction SilentlyContinue
        if (-not $resourceGroup) {
            Write-StatusMessage "Creating resource group $ResourceGroupName in $Location..." -Status "INFO"
            $resourceGroup = New-AzResourceGroup -Name $ResourceGroupName -Location $Location -ErrorAction Stop
            Write-StatusMessage "Resource group created successfully." -Status "SUCCESS"
        }
        else {
            Write-StatusMessage "Using existing resource group $ResourceGroupName." -Status "INFO"
        }
        
        # Get the parameters file path - with better error handling for path resolution
        $scriptDir = $null
        if ($PSScriptRoot) {
            # Use PSScriptRoot if available (PowerShell 3.0+)
            $scriptDir = $PSScriptRoot
            Write-StatusMessage "Using PSScriptRoot for script directory: $scriptDir" -Status "INFO"
        }
        else {
            # Fall back to MyInvocation
            $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
            Write-StatusMessage "Using MyInvocation for script directory: $scriptDir" -Status "INFO"
        }
        
        if (-not $scriptDir) {
            throw "Could not determine script directory. Please run this script from its directory."
        }
        
        $bicepDir = Join-Path -Path $scriptDir -ChildPath "bicep"
        
        # Verify bicep directory exists
        if (-not (Test-Path -Path $bicepDir -PathType Container)) {
            Write-StatusMessage "Bicep directory not found at: $bicepDir" -Status "ERROR"
            Write-StatusMessage "Current script directory: $scriptDir" -Status "INFO"
            Write-StatusMessage "Directory contents:" -Status "INFO"
            Get-ChildItem -Path $scriptDir | ForEach-Object {
                Write-StatusMessage "- $_" -Status "INFO"
            }
            throw "Bicep directory not found at: $bicepDir"
        }
        
        $mainBicepFile = Join-Path -Path $bicepDir -ChildPath "main.bicep"
        $paramsFile = Join-Path -Path $bicepDir -ChildPath "parameters.$Environment.bicepparam"
        
        # Check if files exist with detailed error messages
        if (-not (Test-Path -Path $mainBicepFile -PathType Leaf)) {
            Write-StatusMessage "Main Bicep file not found at: $mainBicepFile" -Status "ERROR"
            Write-StatusMessage "Bicep directory contents:" -Status "INFO"
            Get-ChildItem -Path $bicepDir | ForEach-Object {
                Write-StatusMessage "- $_" -Status "INFO"
            }
            throw "Main Bicep file not found at: $mainBicepFile"
        }
        
        if (-not (Test-Path -Path $paramsFile -PathType Leaf)) {
            Write-StatusMessage "Parameters file not found at: $paramsFile" -Status "WARNING"
            
            # Determine frontend URL based on environment
            $frontendUrl = switch ($Environment) {
                "dev" { "http://localhost:3000" }
                "test" { "https://test.juntosummary.com" }
                "prod" { "https://juntosummary.com" }
                default { "http://localhost:3000" }
            }
            
            # Create parameters file
            Write-StatusMessage "Creating a default parameters file..." -Status "INFO"
            @"
using './main.bicep'

param projectName = 'juntosummary'
param location = '$Location'
param environment = '$Environment'
param frontendUrl = '$frontendUrl'
"@ | Out-File -FilePath $paramsFile -Encoding utf8
            
            Write-StatusMessage "Created default parameters file at: $paramsFile" -Status "SUCCESS"
            
            # Verify the file was created successfully
            if (-not (Test-Path -Path $paramsFile -PathType Leaf)) {
                throw "Failed to create parameters file at: $paramsFile"
            }
        }
        
        # Deploy Bicep template
        $deploymentName = "juntosummary-$Environment-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        
        Write-StatusMessage "Starting deployment of JuntoSummary infrastructure to $Environment..." -Status "INFO"
        Write-StatusMessage "Using Bicep template: $mainBicepFile" -Status "INFO"
        Write-StatusMessage "Using parameters file: $paramsFile" -Status "INFO"
        Write-StatusMessage "This may take several minutes to complete." -Status "INFO"
        
        $deployment = New-AzResourceGroupDeployment `
            -Name $deploymentName `
            -ResourceGroupName $ResourceGroupName `
            -TemplateFile $mainBicepFile `
            -TemplateParameterFile $paramsFile `
            -ErrorAction Stop
        
        # Display deployment results
        if ($deployment.ProvisioningState -eq "Succeeded") {
            Write-StatusMessage "Deployment completed successfully!" -Status "SUCCESS"
            
            # Display important outputs
            Write-StatusMessage "Function App URL: $($deployment.Outputs.functionAppUrl.Value)" -Status "INFO"
            Write-StatusMessage "Swagger UI: $($deployment.Outputs.swaggerUrl.Value)" -Status "INFO"
            Write-StatusMessage "Key Vault: $($deployment.Outputs.keyVaultName.Value)" -Status "INFO"
            
            # Calculate and display deployment time
            $endTime = Get-Date
            $duration = New-TimeSpan -Start $startTime -End $endTime
            Write-StatusMessage "Total deployment time: $($duration.Minutes) minutes and $($duration.Seconds) seconds" -Status "INFO"
            
            # Post-deployment instructions
            Write-StatusMessage "Next steps:" -Status "INFO"
            Write-StatusMessage "1. Update MongoDB connection string in Key Vault" -Status "INFO"
            Write-StatusMessage "2. Deploy your Function App code" -Status "INFO"
            Write-StatusMessage "3. Configure your frontend to use the Function App URL" -Status "INFO"
            
            return $true
        }
        else {
            throw "Deployment failed with state: $($deployment.ProvisioningState)"
        }
    }
    catch {
        Write-StatusMessage "Deployment failed: $_" -Status "ERROR"
        if ($_.Exception.InnerException) {
            Write-StatusMessage "Inner exception: $($_.Exception.InnerException.Message)" -Status "ERROR"
        }
        Write-StatusMessage "Stack Trace:" -Status "ERROR"
        Write-StatusMessage $_.ScriptStackTrace -Status "ERROR"
        Write-StatusMessage "Check the log file for details: $logFile" -Status "INFO"
        return $false
    }
}

function Show-DeploymentMenu {
    Write-Host "`n============================================" -ForegroundColor Cyan
    Write-Host "       JuntoSummary Infrastructure Menu     " -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host
    Write-Host "1. Deploy to Development Environment"
    Write-Host "2. Deploy to Test Environment"
    Write-Host "3. Deploy to Production Environment"
    Write-Host "4. Check Azure Connection"
    Write-Host "5. List Resource Groups"
    Write-Host "6. View Deployment Log"
    Write-Host "7. Verify Infrastructure Files"
    Write-Host "8. Install/Update Bicep CLI"
    Write-Host "C. Clear Screen"
    Write-Host "Q. Quit"
    Write-Host
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "Log file: $logFile" -ForegroundColor DarkGray
}

function Wait-ForContinue {
    Write-Host
    Write-Host "Press Enter to continue..." -ForegroundColor Yellow
    Read-Host | Out-Null
}

function Test-InfrastructureFiles {
    try {
        Write-StatusMessage "Verifying infrastructure files..." -Status "INFO"
        
        # Determine script directory
        $scriptDir = $null
        if ($PSScriptRoot) {
            $scriptDir = $PSScriptRoot
        }
        else {
            $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
        }
        
        if (-not $scriptDir) {
            Write-StatusMessage "Could not determine script directory." -Status "ERROR"
            return $false
        }
        
        Write-StatusMessage "Script directory: $scriptDir" -Status "INFO"
        
        # Check bicep directory
        $bicepDir = Join-Path -Path $scriptDir -ChildPath "bicep"
        if (-not (Test-Path -Path $bicepDir -PathType Container)) {
            Write-StatusMessage "Bicep directory not found at: $bicepDir" -Status "ERROR"
            Write-StatusMessage "Please create the directory and add the required Bicep files." -Status "INFO"
            return $false
        }
        
        Write-StatusMessage "Bicep directory found: $bicepDir" -Status "SUCCESS"
        
        # Check main.bicep
        $mainBicepFile = Join-Path -Path $bicepDir -ChildPath "main.bicep"
        if (-not (Test-Path -Path $mainBicepFile -PathType Leaf)) {
            Write-StatusMessage "Main Bicep file not found at: $mainBicepFile" -Status "ERROR"
            return $false
        }
        
        Write-StatusMessage "Main Bicep file found: $mainBicepFile" -Status "SUCCESS"
        
        # Check module files
        $requiredModules = @('functionApp.bicep', 'storageAccount.bicep', 'appInsights.bicep', 'keyVault.bicep')
        $missingModules = @()
        
        foreach ($module in $requiredModules) {
            $modulePath = Join-Path -Path $bicepDir -ChildPath $module
            if (-not (Test-Path -Path $modulePath -PathType Leaf)) {
                Write-StatusMessage "Module file not found: $module" -Status "ERROR"
                $missingModules += $module
            }
            else {
                Write-StatusMessage "Module file found: $module" -Status "SUCCESS"
            }
        }
        
        if ($missingModules.Count -gt 0) {
            Write-StatusMessage "Missing module files: $($missingModules -join ', ')" -Status "ERROR"
            return $false
        }
        
        # List directory contents for reference
        Write-StatusMessage "All required Bicep files found." -Status "SUCCESS"
        Write-StatusMessage "Bicep directory contents:" -Status "INFO"
        Get-ChildItem -Path $bicepDir | ForEach-Object {
            Write-StatusMessage "- $($_.Name)" -Status "INFO"
        }
        
        return $true
    }
    catch {
        Write-StatusMessage "Error verifying infrastructure files: $_" -Status "ERROR"
        return $false
    }
}

function Test-BicepInstallation {
    Write-StatusMessage "Running detailed Bicep CLI diagnostics..." -Status "INFO"
    
    # Check ALL common Bicep installation locations
    $commonPaths = @(
        # Standard paths the script currently checks
        "$env:ProgramFiles\Bicep",
        "$env:ProgramFiles\Azure\Bicep",
        "$env:LocalAppData\Programs\Bicep",
        
        # ADDITIONAL typical Bicep installation locations
        "$env:LOCALAPPDATA\.azure\bin",                  # Azure CLI bicep location
        "$env:ProgramFiles\Microsoft Bicep CLI",         # MSI/winget install
        "C:\ProgramData\chocolatey\lib\bicep\tools"      # Chocolatey install
    )
    
    $foundInPath = $false
    foreach ($path in $commonPaths) {
        $bicepExePath = Join-Path -Path $path -ChildPath "bicep.exe"
        if (Test-Path $bicepExePath) {
            Write-StatusMessage "Found bicep.exe at: $bicepExePath" -Status "SUCCESS"
            $foundInPath = $true
            
            # Improved PATH check with case-insensitive comparison and trimming trailing backslashes
            $envPaths = $env:PATH -split ';'
            $pathInEnv = $envPaths | Where-Object { $_.TrimEnd('\') -ieq $path.TrimEnd('\') }
            if ($pathInEnv) {
                Write-StatusMessage "This location is in your PATH environment variable." -Status "SUCCESS"
            }
            else {
                Write-StatusMessage "This location is NOT in your PATH environment variable!" -Status "ERROR"
                Write-StatusMessage "To fix this, add this path to your system PATH: $path" -Status "INFO"
            }
        }
    }
    
    if (-not $foundInPath) {
        Write-StatusMessage "Could not find bicep.exe in common installation locations" -Status "WARNING"
    }
    
    # Check for Azure CLI Bicep extension
    try {
        $azCliPath = Get-Command az -ErrorAction SilentlyContinue
        if ($azCliPath) {
            Write-StatusMessage "Azure CLI found at: $($azCliPath.Source)" -Status "INFO"
            
            # Check Azure CLI version first
            $azVersionOutput = & az version 2>&1
            if ($LASTEXITCODE -eq 0) {
                $azVersionMatch = $azVersionOutput | Select-String "azure-cli\s+(\d+\.\d+\.\d+)"
                if ($azVersionMatch) {
                    Write-StatusMessage "Azure CLI version: $($azVersionMatch.Matches.Groups[1].Value)" -Status "SUCCESS" 
                }
                
                # Check for Bicep extension safely
                $bicepExtension = & az extension show -n bicep -o json 2>&1
                if ($LASTEXITCODE -eq 0) {
                    $bicepJson = $bicepExtension | ConvertFrom-Json
                    Write-StatusMessage "Bicep extension is installed for Azure CLI (version $($bicepJson.version))" -Status "SUCCESS"
                    Write-StatusMessage "You can use 'az bicep' commands with the Azure CLI" -Status "INFO"
                }
                else {
                    Write-StatusMessage "Bicep extension is NOT installed for Azure CLI" -Status "WARNING"
                    Write-StatusMessage "You can install it with: az extension add --name bicep" -Status "INFO"
                }
            }
            else {
                Write-StatusMessage "Azure CLI is not working properly: $azVersionOutput" -Status "ERROR"
            }
        }
        else {
            Write-StatusMessage "Azure CLI not found in PATH" -Status "INFO"
        }
    }
    catch {
        Write-StatusMessage "Error checking Azure CLI: $_" -Status "ERROR"
    }
    
    # Try direct bicep command with error capture
    try {
        $bicepVersion = & bicep --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-StatusMessage "Bicep CLI is accessible directly! Version: $bicepVersion" -Status "SUCCESS"
            Write-StatusMessage "Your Bicep installation is working, but may not be properly detected by the script" -Status "INFO"
        }
        else {
            Write-StatusMessage "Bicep CLI command failed: $bicepVersion" -Status "ERROR"
        }
    }
    catch {
        Write-StatusMessage "Error running bicep command: $_" -Status "ERROR"
    }
    
    # Check PowerShell session path
    Write-StatusMessage "Current PowerShell session PATH variable:" -Status "INFO"
    $env:PATH -split ';' | ForEach-Object {
        if ($_ -match 'bicep' -or $_ -match '\.azure') {
            Write-StatusMessage "PATH: $_ (may contain Bicep)" -Status "SUCCESS"
        }
    }
    
    # Quick fix suggestions
    Write-StatusMessage "`nPossible solutions if Bicep is installed but not detected:" -Status "INFO"
    Write-StatusMessage "1. Try restarting your PowerShell session" -Status "INFO"
    Write-StatusMessage "2. Install Bicep via Azure CLI: az bicep install" -Status "INFO"
    Write-StatusMessage "3. Install Bicep manually and add to PATH: https://aka.ms/bicep-install" -Status "INFO"
    Write-StatusMessage "4. Use 'Temporary Fix' below if Bicep is installed but not in PATH" -Status "INFO"
    
    # Provide a temporary PATH fix option
    Write-StatusMessage "`nTemporary Fix (if you already have Bicep installed):" -Status "INFO"
    $foundBicepPath = ""
    foreach ($path in $commonPaths) {
        if (Test-Path (Join-Path -Path $path -ChildPath "bicep.exe")) {
            $foundBicepPath = $path
            break
        }
    }
    
    if ($foundBicepPath) {
        Write-StatusMessage "Run this command to temporarily add Bicep to your PATH:" -Status "SUCCESS"
        Write-StatusMessage "`$env:PATH += ';$foundBicepPath'" -Status "INFO"
    }
}

# Main script execution
Write-StatusMessage "Starting JuntoSummary deployment script" -Status "INFO"
Write-StatusMessage "Log file created at: $logFile" -Status "INFO"

if (-not (Confirm-AzModules)) {
    Write-StatusMessage "Required Azure PowerShell modules are not available. Exiting..." -Status "ERROR"
    Wait-ForContinue
    exit 1
}

do {
    Show-DeploymentMenu
    $selection = Read-Host "Please make a selection"
    
    switch ($selection.ToLower()) {
        '1' {
            Write-StatusMessage "Preparing to deploy to DEVELOPMENT environment..." -Status "INFO"
            
            if (Connect-ToAzure) {
                $result = Deploy-Bicep -Environment "dev"
                if (-not $result) {
                    Write-StatusMessage "Development deployment encountered issues." -Status "WARNING"
                }
            }
            else {
                Write-StatusMessage "Cannot proceed without Azure connection." -Status "ERROR"
            }
            
            Wait-ForContinue
        }
        '2' {
            Write-StatusMessage "Preparing to deploy to TEST environment..." -Status "INFO"
            
            if (Connect-ToAzure) {
                $result = Deploy-Bicep -Environment "test"
                if (-not $result) {
                    Write-StatusMessage "Test deployment encountered issues." -Status "WARNING"
                }
            }
            else {
                Write-StatusMessage "Cannot proceed without Azure connection." -Status "ERROR"
            }
            
            Wait-ForContinue
        }
        '3' {
            Write-StatusMessage "Preparing to deploy to PRODUCTION environment..." -Status "WARNING"
            
            $confirmProd = Read-Host "Are you sure you want to deploy to PRODUCTION? (y/N)"
            if ($confirmProd -eq "y" -or $confirmProd -eq "Y") {
                if (Connect-ToAzure) {
                    # For production, prompt for additional confirmation
                    $subscriptionName = (Get-AzContext).Subscription.Name
                    $confirmSubscription = Read-Host "Confirm deployment to subscription: $subscriptionName (y/N)"
                    
                    if ($confirmSubscription -eq "y" -or $confirmSubscription -eq "Y") {
                        $result = Deploy-Bicep -Environment "prod"
                        if (-not $result) {
                            Write-StatusMessage "Production deployment encountered issues." -Status "WARNING"
                        }
                    }
                    else {
                        Write-StatusMessage "Production deployment canceled by user." -Status "INFO"
                    }
                }
                else {
                    Write-StatusMessage "Cannot proceed without Azure connection." -Status "ERROR"
                }
            }
            else {
                Write-StatusMessage "Production deployment canceled by user." -Status "INFO"
            }
            
            Wait-ForContinue
        }
        '4' {
            Write-StatusMessage "Checking Azure connection..." -Status "INFO"
            
            if (Connect-ToAzure) {
                $context = Get-AzContext
                
                Write-Host
                Write-Host "Azure Connection Details:" -ForegroundColor Cyan
                Write-Host "------------------------" -ForegroundColor Cyan
                Write-Host "Account:      $($context.Account.Id)"
                Write-Host "Subscription: $($context.Subscription.Name)"
                Write-Host "Tenant:       $($context.Tenant.Id)"
                Write-Host "Environment:  $($context.Environment.Name)"
            }
            else {
                Write-StatusMessage "Failed to connect to Azure." -Status "ERROR"
            }
            
            Wait-ForContinue
        }
        '5' {
            Write-StatusMessage "Listing resource groups..." -Status "INFO"
            
            if (Connect-ToAzure) {
                try {
                    $resourceGroups = Get-AzResourceGroup | Where-Object { $_.ResourceGroupName -like "*juntosummary*" }
                    
                    if ($resourceGroups -and $resourceGroups.Count -gt 0) {
                        Write-Host
                        Write-Host "JuntoSummary Resource Groups:" -ForegroundColor Cyan
                        Write-Host "-----------------------------" -ForegroundColor Cyan
                        $resourceGroups | Format-Table ResourceGroupName, Location, Tags
                    }
                    else {
                        Write-StatusMessage "No JuntoSummary resource groups found." -Status "INFO"
                    }
                }
                catch {
                    Write-StatusMessage "Failed to list resource groups: $_" -Status "ERROR"
                }
            }
            else {
                Write-StatusMessage "Cannot list resource groups without Azure connection." -Status "ERROR"
            }
            
            Wait-ForContinue
        }
        '6' {
            if (Test-Path $logFile) {
                Write-StatusMessage "Opening deployment log..." -Status "INFO"
                Get-Content $logFile | Out-Host
            }
            else {
                Write-StatusMessage "Log file not found: $logFile" -Status "ERROR"
            }
            
            Wait-ForContinue
        }
        '7' {
            Write-StatusMessage "Verifying infrastructure files..." -Status "INFO"
            $result = Test-InfrastructureFiles
            if ($result) {
                Write-StatusMessage "All required infrastructure files are present." -Status "SUCCESS"
            }
            else {
                Write-StatusMessage "Some infrastructure files are missing. Check the logs for details." -Status "ERROR"
            }
            
            Wait-ForContinue
        }
        '8' {
            Write-StatusMessage "Installing/Updating Bicep CLI..." -Status "INFO"
            
            # First try the regular check
            $result = Confirm-BicepInstalled
            if ($result) {
                Write-StatusMessage "Bicep CLI is installed and ready to use." -Status "SUCCESS"
            }
            else {
                Write-StatusMessage "Running advanced diagnostics for Bicep installation..." -Status "INFO"
                Test-BicepInstallation
            }
            
            Wait-ForContinue
        }
        'c' {
            Clear-Host
            Write-StatusMessage "Screen cleared. Returning to menu..." -Status "INFO"
        }
        'q' {
            Write-StatusMessage "Exiting JuntoSummary deployment script." -Status "INFO"
            return
        }
        default {
            Write-StatusMessage "Invalid selection. Please try again." -Status "WARNING"
            Start-Sleep -Seconds 1
        }
    }
} while ($true)