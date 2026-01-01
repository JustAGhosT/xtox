<#
.SYNOPSIS
    Deploys the XToPDF infrastructure to Azure.
.DESCRIPTION
    This script deploys all the infrastructure components for XToPDF using Bicep templates.
.PARAMETER Environment
    The environment to deploy to (dev, test, prod).
.PARAMETER Location
    The Azure region to deploy to.
.PARAMETER ResourceGroupName
    The name of the resource group to deploy to.
.PARAMETER SubscriptionId
    The ID of the Azure subscription to deploy to.
.EXAMPLE
    ./deploy.ps1 -Environment dev -Location eastus
.EXAMPLE
    ./deploy.ps1 -Environment prod -Location westus -ResourceGroupName "xtopdf-prod-rg" -SubscriptionId "00000000-0000-0000-0000-000000000000"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("dev", "test", "prod")]
    [string]$Environment,

    [Parameter(Mandatory = $false)]
    [string]$Location = "eastus",

    [Parameter(Mandatory = $false)]
    [string]$ResourceGroupName = "",

    [Parameter(Mandatory = $false)]
    [string]$SubscriptionId = ""
)

# Start timing the deployment
$deploymentStartTime = Get-Date

# Set error action preference
$ErrorActionPreference = "Stop"

# Initialize variables
if ([string]::IsNullOrEmpty($ResourceGroupName)) {
    $ResourceGroupName = "xtopdf-$Environment-rg"
}

# Functions
function Write-Status {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Message,
        
        [Parameter(Mandatory = $false)]
        [string]$Status = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $statusColor = switch ($Status) {
        "INFO" { "Cyan" }
        "SUCCESS" { "Green" }
        "WARNING" { "Yellow" }
        "ERROR" { "Red" }
        default { "White" }
    }
    
    Write-Host "[$timestamp] [$Status] $Message" -ForegroundColor $statusColor
}

try {
    Write-Status "Starting deployment for environment: $Environment"
    
    # Set the subscription context if provided
    if (-not [string]::IsNullOrEmpty($SubscriptionId)) {
        Write-Status "Setting subscription context to $SubscriptionId"
        $subscriptionContext = Set-AzContext -SubscriptionId $SubscriptionId
        if (-not $subscriptionContext) {
            throw "Failed to set subscription context. Please check your subscription ID and ensure you're logged in."
        }
    }
    
    # Check if user is logged in to Azure
    $azContext = Get-AzContext
    if (-not $azContext) {
        Write-Status "You are not logged in to Azure. Please run Connect-AzAccount first." -Status "ERROR"
        exit 1
    }
    
    Write-Status "Connected to Azure as $($azContext.Account.Id) on subscription $($azContext.Subscription.Name)"
    
    # Create resource group if it doesn't exist
    $resourceGroup = Get-AzResourceGroup -Name $ResourceGroupName -ErrorAction SilentlyContinue
    if (-not $resourceGroup) {
        Write-Status "Creating resource group $ResourceGroupName in $Location"
        $resourceGroup = New-AzResourceGroup -Name $ResourceGroupName -Location $Location
        Write-Status "Resource group created successfully" -Status "SUCCESS"
    }
    else {
        Write-Status "Using existing resource group $ResourceGroupName"
    }
    
    # Get the path to the Bicep template and parameters file
    $scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    $bicepPath = Join-Path -Path (Split-Path -Parent $scriptPath) -ChildPath "bicep"
    $mainBicepFile = Join-Path -Path $bicepPath -ChildPath "main.bicep"
    $parametersFile = Join-Path -Path $bicepPath -ChildPath "parameters.$Environment.bicepparam"
    
    # Verify that files exist
    if (-not (Test-Path $mainBicepFile)) {
        throw "Main Bicep file not found at $mainBicepFile"
    }
    
    if (-not (Test-Path $parametersFile)) {
        throw "Parameters file not found at $parametersFile"
    }
    
    # Deploy the Bicep template
    Write-Status "Deploying Bicep template to resource group $ResourceGroupName"
    $deploymentName = "xtopdf-$Environment-$(Get-Date -Format 'yyyyMMddHHmmss')"
    
    $deployment = New-AzResourceGroupDeployment `
        -Name $deploymentName `
        -ResourceGroupName $ResourceGroupName `
        -TemplateFile $mainBicepFile `
        -TemplateParameterFile $parametersFile `
        -Mode Incremental `
        -Verbose
    
    if ($deployment.ProvisioningState -eq "Succeeded") {
        Write-Status "Deployment completed successfully" -Status "SUCCESS"
        
        # Output deployment results
        Write-Status "Deployment outputs:"
        $deployment.Outputs | ForEach-Object {
            $_.GetEnumerator() | ForEach-Object {
                Write-Status "$($_.Key): $($_.Value.Value)" -Status "INFO"
            }
        }
        
        # Calculate and display deployment duration
        $deploymentEndTime = Get-Date
        $deploymentDuration = $deploymentEndTime - $deploymentStartTime
        Write-Status "Total deployment time: $($deploymentDuration.ToString('hh\:mm\:ss'))" -Status "INFO"
    }
    else {
        throw "Deployment failed with state: $($deployment.ProvisioningState)"
    }
}
catch {
    Write-Status "Deployment failed with error: $_" -Status "ERROR"
    
    # Get more details about the error if available
    if ($PSItem.Exception.InnerException) {
        Write-Status "Inner exception: $($PSItem.Exception.InnerException.Message)" -Status "ERROR"
    }
    
    if ($PSItem.ScriptStackTrace) {
        Write-Status "Stack trace: $($PSItem.ScriptStackTrace)" -Status "ERROR"
    }
    
    exit 1
}