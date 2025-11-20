@description('Name of the storage account')
param name string

@description('Location for the storage account')
param location string

@description('Environment (dev, test, prod)')
param environment string

@description('Project name')
param projectName string

// SKU depends on environment
var storageSku = environment == 'prod' ? 'Standard_GRS' : 'Standard_LRS'

resource storageAccount 'Microsoft.Storage/storageAccounts@2022-05-01' = {
  name: name
  location: location
  kind: 'StorageV2'
  sku: {
    name: storageSku
  }
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    accessTier: 'Hot'
    allowBlobPublicAccess: false
  }
  tags: {
    environment: environment
    project: projectName
  }
}

// Create blob services and containers
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2022-05-01' = {
  name: 'default'
  parent: storageAccount
}

resource documents 'Microsoft.Storage/storageAccounts/blobServices/containers@2022-05-01' = {
  name: 'documents'
  parent: blobService
  properties: {
    publicAccess: 'None'
  }
}

resource pdfs 'Microsoft.Storage/storageAccounts/blobServices/containers@2022-05-01' = {
  name: 'pdfs'
  parent: blobService
  properties: {
    publicAccess: 'None'
  }
}

// Get the connection string
var connectionString = 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${storageAccount.listKeys().keys[0].value}'

// Outputs
output name string = storageAccount.name
output connectionString string = connectionString
