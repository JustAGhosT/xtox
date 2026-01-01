targetScope = 'resourceGroup'

// Parameters
@description('Project name to be used in resource names')
param projectName string = 'juntosummary'
@description('Location for all resources')
param location string = 'westeurope'

@description('Environment (dev, test, prod)')
@allowed([
  'dev'
  'test'
  'prod'
])
param environment string = 'dev'

@description('Frontend URL for CORS configuration')
param frontendUrl string

// Variables for resource naming following [env]-[loc]-resourcetype-[proj] pattern
var shortLocation = 'we' // Short form of westeurope
var functionAppName = '${environment}-${shortLocation}-func-${projectName}'
var storageAccountName = '${environment}${shortLocation}st${projectName}'
var appInsightsName = '${environment}-${shortLocation}-ai-${projectName}'
var hostingPlanName = '${environment}-${shortLocation}-plan-${projectName}'
var keyVaultName = '${environment}-${shortLocation}-kv-${projectName}'
// Resources
module storageAccount 'storageAccount.bicep' = {
  name: 'storageAccountDeploy'
  params: {
    name: storageAccountName
    location: location
    environment: environment
    projectName: projectName
  }
}

module appInsights 'appInsights.bicep' = {
  name: 'appInsightsDeploy'
  params: {
    name: appInsightsName
    location: location
    environment: environment
    projectName: projectName
  }
}

module functionApp 'functionApp.bicep' = {
  name: 'functionAppDeploy'
  params: {
    name: functionAppName
    location: location
    environment: environment
    projectName: projectName
    hostingPlanName: hostingPlanName
    storageAccountName: storageAccount.outputs.name
    storageAccountConnectionString: storageAccount.outputs.connectionString
    appInsightsKey: appInsights.outputs.instrumentationKey
    frontendUrl: frontendUrl
  }
}

module keyVault 'keyVault.bicep' = {
  name: 'keyVaultDeploy'
  params: {
    name: keyVaultName
    location: location
    environment: environment
    projectName: projectName
    functionAppPrincipalId: functionApp.outputs.principalId
  }
}

// Outputs
output functionAppName string = functionApp.outputs.name
output functionAppHostName string = functionApp.outputs.hostName
output functionAppUrl string = 'https://${functionApp.outputs.hostName}'
output swaggerUrl string = 'https://${functionApp.outputs.hostName}/api/docs'
output storageAccountName string = storageAccount.outputs.name
output keyVaultName string = keyVault.outputs.name
