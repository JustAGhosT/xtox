<#
.SYNOPSIS
    Deploys the JuntoSummary infrastructure to Azure using Bicep templates.
.DESCRIPTION
    This script deploys all necessary Azure resources for the JuntoSummary application including:
    - Azure Function App with FastAPI and Swagger
    - Storage Account for document storage and Function runtime
    - Application Insights for monitoring
    - Key Vault for secrets management
.PARAMETER Environment
    The deployment environment (dev, test, prod)
.PARAMETER Location
    The Azure region for deployment (defaults to westeurope)
.PARAMETER ResourceGroupName
    Optional custom resource group name. If not specified, uses [env]-[loc]-rg-juntosummary
.EXAMPLE
    .\deploy.ps1 -Environment dev
.EXAMPLE
    .\deploy.ps1 -Environment prod -Location westeurope
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("dev", "test", "prod")]
    [string]$Environment,

    [Parameter(Mandatory = $false)]
    [string]$Location = "westeurope",

    [Parameter(Mandatory = $false)]
    [string]$ResourceGroupName = ""
)

# Start timing deployment
$startTime = Get-Date
$shortLocation = "euw" # Short form of westeurope

# Set default resource group name if not provided
if ([string]::IsNullOrEmpty($ResourceGroupName)) {
    $ResourceGroupName = "$Environment-$shortLocation-rg-juntosummary"
}

# Function to format status messages
function Write-Status {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Message,
        
        [Parameter(Mandatory = $false)]
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
    
    Write-Host "[$timestamp] [$Status] $Message" -ForegroundColor $color
}

try {
    # Check Azure connection
    try {
        $context = Get-AzContext -ErrorAction Stop
        if (-not $context) {
            Write-Status "Not connected to Azure. Please run Connect-AzAccount." -Status "ERROR"
            exit 1
        }
        Write-Status "Connected to Azure as $($context.Account.Id) on subscription $($context.Subscription.Name)" -Status "INFO"
    }
    catch {
        Write-Status "Error checking Azure connection. Make sure Az PowerShell module is installed." -Status "ERROR"
        Write-Status "Install with: Install-Module -Name Az -Scope CurrentUser -Repository PSGallery -Force" -Status "INFO"
        exit 1
    }

    # Create or check resource group
    try {
        $resourceGroup = Get-AzResourceGroup -Name $ResourceGroupName -ErrorAction SilentlyContinue
        if (-not $resourceGroup) {
            Write-Status "Creating resource group $ResourceGroupName in $Location..." -Status "INFO"
            $resourceGroup = New-AzResourceGroup -Name $ResourceGroupName -Location $Location
            Write-Status "Resource group created successfully." -Status "SUCCESS"
        } else {
            Write-Status "Using existing resource group $ResourceGroupName." -Status "INFO"
        }
    }
    catch {
        Write-Status "Failed to create or access resource group: $_" -Status "ERROR"
        exit 1
    }

    # Get the parameters file path
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $bicepDir = Join-Path $scriptDir "bicep"
    $mainBicepFile = Join-Path $bicepDir "main.bicep"
    $paramsFile = Join-Path $bicepDir "parameters.$Environment.bicepparam"

    # Check if files exist
    if (-not (Test-Path $mainBicepFile)) {
        Write-Status "Main Bicep file not found at: $mainBicepFile" -Status "ERROR"
        exit 1
    }

    if (-not (Test-Path $paramsFile)) {
        Write-Status "Parameters file not found at: $paramsFile" -Status "ERROR"
        Write-Status "Creating a default parameters file..." -Status "WARNING"
        
        $frontendUrl = switch ($Environment) {
            "dev" { "http://localhost:3000" }
            "test" { "https://test.juntosummary.com" }
            "prod" { "https://juntosummary.com" }
            default { "http://localhost:3000" }
        }

        @"
using './main.bicep'

param projectName = 'juntosummary'
param location = '$Location'
param environment = '$Environment'
param frontendUrl = '$frontendUrl'
"@ | Out-File -FilePath $paramsFile -Encoding utf8
        
        Write-Status "Created default parameters file at: $paramsFile" -Status "SUCCESS"
    }

    # Deploy Bicep template
    $deploymentName = "juntosummary-$Environment-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    
    Write-Status "Starting deployment of JuntoSummary infrastructure to $Environment..." -Status "INFO"
    Write-Status "This may take several minutes to complete." -Status "INFO"
    
    try {
        $deployment = New-AzResourceGroupDeployment `
            -Name $deploymentName `
            -ResourceGroupName $ResourceGroupName `
            -TemplateFile $mainBicepFile `
            -TemplateParameterFile $paramsFile `
            -Verbose
        
        if ($deployment.ProvisioningState -eq "Succeeded") {
            Write-Status "Deployment completed successfully!" -Status "SUCCESS"
            
            # Display important outputs
            Write-Status "Function App URL: $($deployment.Outputs.functionAppUrl.Value)" -Status "INFO"
            Write-Status "Swagger UI: $($deployment.Outputs.swaggerUrl.Value)" -Status "INFO"
            Write-Status "Key Vault: $($deployment.Outputs.keyVaultName.Value)" -Status "INFO"
            
            # Calculate and display deployment time
            $endTime = Get-Date
            $duration = New-TimeSpan -Start $startTime -End $endTime
            Write-Status "Total deployment time: $($duration.Minutes) minutes and $($duration.Seconds) seconds" -Status "INFO"
        } else {
            Write-Status "Deployment failed with state: $($deployment.ProvisioningState)" -Status "ERROR"
        }
    }
    catch {
        Write-Status "Deployment failed with error: $_" -Status "ERROR"
        exit 1
    }

    # Post-deployment instructions
    Write-Status "Next steps:" -Status "INFO"
    Write-Status "1. Update MongoDB connection string in Key Vault" -Status "INFO"
    Write-Status "2. Deploy your Function App code" -Status "INFO"
    Write-Status "3. Configure your frontend to use the Function App URL" -Status "INFO"
}
catch {
    Write-Status "An error occurred: $_" -Status "ERROR"
    if ($_.Exception.InnerException) {
        Write-Status "Inner exception: $($_.Exception.InnerException.Message)" -Status "ERROR"
    }
    exit 1
}