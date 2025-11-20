@description('Name of the function app')
param name string

@description('Location for the function app')
param location string

@description('Environment (dev, test, prod)')
param environment string

@description('Project name')
param projectName string

@description('Name of the hosting plan')
param hostingPlanName string

@description('Name of the storage account')
param storageAccountName string

@description('Connection string for the storage account')
@secure()
param storageAccountConnectionString string

@description('Application Insights instrumentation key')
@secure()
param appInsightsKey string

@description('Frontend URL for CORS configuration')
param frontendUrl string

var tier = environment == 'prod' ? 'P1v2' : 'B1'
var shortLocation = 'we' // Short form of westeurope
var kvName = '${environment}-${shortLocation}-kv-${projectName}'
var mongoDbConnectionString = '@Microsoft.KeyVault(SecretUri=https://${kvName}.vault.azure.net/secrets/MongoDbConnectionString/)'
var dbName = environment == 'prod' ? 'juntosummary' : 'juntosummary-${environment}'

resource hostingPlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: hostingPlanName
  location: location
  sku: {
    name: tier
  }
  properties: {
    reserved: true // For Linux
  }
  kind: 'linux'
}
    environment: environment
    project: projectName
  }
}
resource functionApp 'Microsoft.Web/sites@2022-03-01' = {
  name: name
  location: location
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: hostingPlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.9'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      cors: {
        allowedOrigins: [
          frontendUrl
        ]
        supportCredentials: true
      }
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: storageAccountConnectionString
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsightsKey
        }
        {
          name: 'MONGO_URL'
          value: mongoDbConnectionString
        }
        {
          name: 'DB_NAME'
          value: dbName
        }
        {
          name: 'FRONTEND_URL'
          value: frontendUrl
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'ENABLE_ORYX_BUILD'
          value: 'true'
        }
      ]
    }
  }
}
  tags: {
    environment: environment
    project: projectName
    'hidden-link: /app-insights-resource-id': resourceId('Microsoft.Insights/components', '${environment}-${shortLocation}-ai-${projectName}')
  }
}
output name string = functionApp.name
output hostName string = functionApp.properties.defaultHostName
output principalId string = functionApp.identity.principalId
