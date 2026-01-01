@description('Name of the Key Vault')
param name string

@description('Location for the Key Vault')
param location string

@description('Environment (dev, test, prod)')
param environment string

@description('Project name')
param projectName string

@description('Principal ID of the Function App')
param functionAppPrincipalId string

resource keyVault 'Microsoft.KeyVault/vaults@2022-07-01' = {
  name: name
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: false
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enabledForTemplateDeployment: true
    accessPolicies: [
      {
        tenantId: subscription().tenantId
        objectId: functionAppPrincipalId
        permissions: {
          secrets: [
            'get'
            'list'
          ]
        }
      }
    ]
  }
  tags: {
    environment: environment
    project: projectName
  }
}

// Create a placeholder secret for MongoDB connection string
// In production, you'd replace this with the actual value via script or Azure Portal
resource mongoConnectionString 'Microsoft.KeyVault/vaults/secrets@2022-07-01' = {
  name: 'MongoDbConnectionString'
  parent: keyVault
  properties: {
    value: 'mongodb://placeholder:placeholder@localhost:27017'
    contentType: 'text/plain'
  }
}

output name string = keyVault.name
