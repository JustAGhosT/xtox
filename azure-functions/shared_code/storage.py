import os
import logging
from datetime import datetime, timedelta
import io

# Azure Storage imports
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, generate_blob_sas, BlobSasPermissions
from azure.storage.filedatalake import DataLakeServiceClient
from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError

# Azure Storage connection
AZURE_STORAGE_CONNECTION_STRING = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
AZURE_STORAGE_CONTAINER_NAME = os.environ.get('AZURE_STORAGE_CONTAINER_NAME', 'documents')
AZURE_STORAGE_ACCOUNT_NAME = os.environ.get('AZURE_STORAGE_ACCOUNT_NAME')
AZURE_STORAGE_ACCOUNT_KEY = os.environ.get('AZURE_STORAGE_ACCOUNT_KEY')

# Initialize Azure Storage clients
blob_service_client = None
container_client = None
datalake_service_client = None

def initialize_storage():
    """Initialize Azure Storage connections"""
    global blob_service_client, container_client, datalake_service_client
    
    if not AZURE_STORAGE_CONNECTION_STRING:
        raise ValueError("Azure Storage connection string is not configured")
    
    try:
        # Initialize Blob Storage client
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER_NAME)
        
        # Create container if it doesn't exist
        try:
            if not container_client.exists():
                container_client.create_container()
                logging.info(f"Created container: {AZURE_STORAGE_CONTAINER_NAME}")
        except ResourceExistsError:
            pass
        
        # Initialize Data Lake Storage client
        datalake_service_client = DataLakeServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        
        logging.info("Azure Storage clients initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing Azure Storage: {e}")
        raise

def get_blob_service_client():
    """Get or initialize the BlobServiceClient"""
    global blob_service_client
    if blob_service_client is None:
        initialize_storage()
    return blob_service_client

def get_container_client():
    """Get or initialize the ContainerClient"""
    global container_client
    if container_client is None:
        initialize_storage()
    return container_client

def get_datalake_service_client():
    """Get or initialize the DataLakeServiceClient"""
    global datalake_service_client
    if datalake_service_client is None:
        initialize_storage()
    return datalake_service_client

async def store_file(file_content, blob_name, content_type):
    """Store file in Azure Blob Storage"""
    try:
        container = get_container_client()
        blob_client = container.get_blob_client(blob_name)
        
        if isinstance(file_content, bytes):
            # Upload as bytes
            blob_client.upload_blob(file_content, overwrite=True, content_settings={"content_type": content_type})
        else:
            # Convert to bytes if not already
            blob_client.upload_blob(file_content.read(), overwrite=True, content_settings={"content_type": content_type})
        
        return blob_name
    except Exception as e:
        logging.error(f"Error uploading to Azure Storage: {e}")
        raise

async def get_file(blob_name):
    """Get file from Azure Blob Storage"""
    try:
        container = get_container_client()
        blob_client = container.get_blob_client(blob_name)
        download_stream = blob_client.download_blob()
        content_type = download_stream.properties.content_settings.content_type
        
        # Read entire blob content
        content = await download_stream.readall()
        return content, content_type
    except ResourceNotFoundError:
        logging.error(f"Blob not found: {blob_name}")
        raise
    except Exception as e:
        logging.error(f"Error downloading from Azure Storage: {e}")
        raise

async def delete_file(blob_name):
    """Delete file from Azure Blob Storage"""
    try:
        container = get_container_client()
        blob_client = container.get_blob_client(blob_name)
        blob_client.delete_blob()
        return True
    except ResourceNotFoundError:
        logging.warning(f"Blob not found during deletion: {blob_name}")
        return False
    except Exception as e:
        logging.error(f"Error deleting from Azure Storage: {e}")
        raise

def generate_sas_url(blob_name, expiry_hours=1):
    """Generate a SAS URL for temporary access to a blob"""
    try:
        # Create a SAS token
        sas_token = generate_blob_sas(
            account_name=AZURE_STORAGE_ACCOUNT_NAME,
            container_name=AZURE_STORAGE_CONTAINER_NAME,
            blob_name=blob_name,
            account_key=AZURE_STORAGE_ACCOUNT_KEY,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
        )
        
        # Construct the full URL
        sas_url = f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{AZURE_STORAGE_CONTAINER_NAME}/{blob_name}?{sas_token}"
        return sas_url
    except Exception as e:
        logging.error(f"Error generating SAS URL: {e}")
        raise