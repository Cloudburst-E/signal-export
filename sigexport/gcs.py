"""
The purpose of this module is to interact with Google Cloud Storage (GCS) to upload and download files.
"""
from google.cloud import storage
import os
import logging


logger = logging.getLogger(__name__)


class GCSClient:
    """
    A class to interact with Google Cloud Storage (GCS) to upload and download files.
    
    Example usage:
    gcs_client = GCSClient()
    gcs_client.upload_message_media_file('/chat/data.json', 'data.json')
    """
    def __init__(self):
        self.client = storage.Client(project=os.getenv('GCP_PROJECT_ID'))
        self.bucket = self.client.get_bucket(os.getenv('MEDIA_GCS_BUCKET'))

    def blob_exists(self, gcs_filepath):
        """
        Check if a blob exists in the GCS bucket.
        
        args:
            gcs_filepath (str): The GCS filepath to check (without 'gs://{bucket_name}/).
        
        returns:
            bool: True if the blob exists, False otherwise.
        """
        blob = self.bucket.blob(gcs_filepath)
        return blob.exists()

    def upload_message_media_file(self,local_filepath, gcs_filepath, overwrite=False):
        """
        Upload a message media file to GCS.

        args:
            local_filepath (str): The local path to the message media file.
            gcs_filepath (str): The GCS filepath to upload the message media file to (without 'gs://{bucket_name}/).
        
        returns:
            None
        """
        blob = self.bucket.blob(gcs_filepath)

        # Don't upload if it is already in GCS
        if blob.exists() and not overwrite:
            logger.warning(f'GCS message media file already exists at {gcs_filepath} '
                           f'(size {blob.size} bytes).')
            return

        # Upload the file to GCS
        blob.upload_from_filename(local_filepath)
        logger.info(f'Successfully uploaded message media file to GCS at {gcs_filepath} '
                    f'(size {blob.size} bytes).')