"""
Storage Manager for Voice Stream Application
Handles both local file storage and AWS S3 storage based on configuration
"""

import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv
import logging
from typing import Optional, Union, BinaryIO
import tempfile

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StorageManager:
    """
    Manages file storage operations for both local filesystem and AWS S3
    """

    def __init__(self):
        # Storage configuration from environment variables
        self.storage_mode = os.getenv('STORAGE_MODE', 'local').lower()  # 'local' or 's3'

        # S3 Configuration
        self.s3_bucket = os.getenv('S3_BUCKET_NAME')
        self.s3_region = os.getenv('S3_REGION', 'us-east-1')
        self.s3_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.s3_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')

        # Local storage configuration
        self.local_base_path = os.getenv('LOCAL_STORAGE_PATH', os.getcwd())

        # Initialize S3 client if using S3 storage
        self.s3_client = None
        if self.storage_mode == 's3':
            self._initialize_s3_client()

    def _initialize_s3_client(self):
        """Initialize AWS S3 client with error handling"""
        try:
            if self.s3_access_key and self.s3_secret_key:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.s3_access_key,
                    aws_secret_access_key=self.s3_secret_key,
                    region_name=self.s3_region
                )
            else:
                # Use default credentials (IAM role, environment, or ~/.aws/credentials)
                self.s3_client = boto3.client('s3', region_name=self.s3_region)

            # Test S3 connection
            self._test_s3_connection()
            logger.info(f"✅ S3 client initialized successfully for bucket: {self.s3_bucket}")

        except NoCredentialsError:
            logger.error("❌ AWS credentials not found. Falling back to local storage.")
            self.storage_mode = 'local'
        except Exception as e:
            logger.error(f"❌ Failed to initialize S3 client: {str(e)}. Falling back to local storage.")
            self.storage_mode = 'local'

    def _test_s3_connection(self):
        """Test S3 connection and bucket access"""
        if not self.s3_bucket:
            raise ValueError("S3_BUCKET_NAME not configured")

        try:
            self.s3_client.head_bucket(Bucket=self.s3_bucket)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                raise ValueError(f"S3 bucket '{self.s3_bucket}' does not exist")
            elif error_code == '403':
                raise ValueError(f"Access denied to S3 bucket '{self.s3_bucket}'")
            else:
                raise e

    def save_file(self, file_content: Union[bytes, BinaryIO], file_path: str) -> str:
        """
        Save file to configured storage (local or S3)

        Args:
            file_content: File content as bytes or file-like object
            file_path: Relative path where file should be saved

        Returns:
            str: Full path/URL where file was saved
        """
        if self.storage_mode == 's3':
            return self._save_to_s3(file_content, file_path)
        else:
            return self._save_to_local(file_content, file_path)

    def load_file(self, file_path: str) -> Optional[bytes]:
        """
        Load file from configured storage

        Args:
            file_path: Path to the file

        Returns:
            bytes: File content or None if not found
        """
        if self.storage_mode == 's3':
            return self._load_from_s3(file_path)
        else:
            return self._load_from_local(file_path)

    def delete_file(self, file_path: str) -> bool:
        """
        Delete file from configured storage

        Args:
            file_path: Path to the file

        Returns:
            bool: True if successful, False otherwise
        """
        if self.storage_mode == 's3':
            return self._delete_from_s3(file_path)
        else:
            return self._delete_from_local(file_path)

    def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists in configured storage

        Args:
            file_path: Path to check

        Returns:
            bool: True if file exists
        """
        if self.storage_mode == 's3':
            return self._s3_file_exists(file_path)
        else:
            return self._local_file_exists(file_path)

    def get_file_url(self, file_path: str, expiration: int = 3600) -> Optional[str]:
        """
        Get URL for file access

        Args:
            file_path: Path to the file
            expiration: URL expiration time in seconds (for S3 only)

        Returns:
            str: URL for file access
        """
        if self.storage_mode == 's3':
            return self._get_s3_presigned_url(file_path, expiration)
        else:
            return self._get_local_file_path(file_path)

    # S3 Storage Methods
    def _save_to_s3(self, file_content: Union[bytes, BinaryIO], file_path: str) -> str:
        """Save file to S3 bucket"""
        try:
            if hasattr(file_content, 'read'):
                # File-like object
                file_content = file_content.read()

            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=file_path,
                Body=file_content,
                ContentType=self._get_content_type(file_path)
            )

            s3_url = f"s3://{self.s3_bucket}/{file_path}"
            logger.info(f"✅ File saved to S3: {s3_url}")
            return s3_url

        except Exception as e:
            logger.error(f"❌ Failed to save file to S3: {str(e)}")
            raise e

    def _load_from_s3(self, file_path: str) -> Optional[bytes]:
        """Load file from S3 bucket"""
        try:
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=file_path)
            return response['Body'].read()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"File not found in S3: {file_path}")
                return None
            else:
                logger.error(f"❌ Failed to load file from S3: {str(e)}")
                raise e

    def _delete_from_s3(self, file_path: str) -> bool:
        """Delete file from S3 bucket"""
        try:
            self.s3_client.delete_object(Bucket=self.s3_bucket, Key=file_path)
            logger.info(f"✅ File deleted from S3: {file_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete file from S3: {str(e)}")
            return False

    def _s3_file_exists(self, file_path: str) -> bool:
        """Check if file exists in S3"""
        try:
            self.s3_client.head_object(Bucket=self.s3_bucket, Key=file_path)
            return True
        except ClientError:
            return False

    def _get_s3_presigned_url(self, file_path: str, expiration: int = 3600) -> Optional[str]:
        """Generate presigned URL for S3 file access"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.s3_bucket, 'Key': file_path},
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            logger.error(f"❌ Failed to generate presigned URL: {str(e)}")
            return None

    # Local Storage Methods
    def _save_to_local(self, file_content: Union[bytes, BinaryIO], file_path: str) -> str:
        """Save file to local filesystem"""
        full_path = os.path.join(self.local_base_path, file_path)

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        try:
            with open(full_path, 'wb') as f:
                if hasattr(file_content, 'read'):
                    f.write(file_content.read())
                else:
                    f.write(file_content)

            logger.info(f"✅ File saved locally: {full_path}")
            return full_path

        except Exception as e:
            logger.error(f"❌ Failed to save file locally: {str(e)}")
            raise e

    def _load_from_local(self, file_path: str) -> Optional[bytes]:
        """Load file from local filesystem"""
        full_path = os.path.join(self.local_base_path, file_path)

        try:
            with open(full_path, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"File not found locally: {full_path}")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to load file locally: {str(e)}")
            raise e

    def _delete_from_local(self, file_path: str) -> bool:
        """Delete file from local filesystem"""
        full_path = os.path.join(self.local_base_path, file_path)

        try:
            if os.path.exists(full_path):
                os.remove(full_path)
                logger.info(f"✅ File deleted locally: {full_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {full_path}")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to delete file locally: {str(e)}")
            return False

    def _local_file_exists(self, file_path: str) -> bool:
        """Check if file exists locally"""
        full_path = os.path.join(self.local_base_path, file_path)
        return os.path.exists(full_path)

    def _get_local_file_path(self, file_path: str) -> str:
        """Get full local file path"""
        return os.path.join(self.local_base_path, file_path)

    def _get_content_type(self, file_path: str) -> str:
        """Get content type based on file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        content_types = {
            '.wav': 'audio/wav',
            '.mp3': 'audio/mpeg',
            '.webm': 'audio/webm',
            '.m4a': 'audio/mp4',
            '.flac': 'audio/flac',
            '.ogg': 'audio/ogg'
        }
        return content_types.get(ext, 'application/octet-stream')

    def get_storage_info(self) -> dict:
        """Get current storage configuration info"""
        return {
            'storage_mode': self.storage_mode,
            's3_bucket': self.s3_bucket if self.storage_mode == 's3' else None,
            's3_region': self.s3_region if self.storage_mode == 's3' else None,
            'local_base_path': self.local_base_path if self.storage_mode == 'local' else None,
            's3_available': self.s3_client is not None
        }

# Global storage manager instance
storage_manager = StorageManager()
