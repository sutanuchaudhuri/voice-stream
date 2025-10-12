"""
Database Manager for Voice Stream Application
Handles both SQLite3 and DynamoDB storage based on configuration
"""

import os
import sqlite3
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, List, Any
import json
from datetime import datetime
import time

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages database operations for both SQLite3 and DynamoDB
    """

    def __init__(self):
        # Database configuration from environment variables
        self.db_mode = os.getenv('DATABASE_MODE', 'sqlite').lower()  # 'sqlite' or 'dynamodb'

        # SQLite Configuration
        self.sqlite_db_path = os.getenv('SQLITE_DB_PATH', 'audio_annotations.db')

        # DynamoDB Configuration
        self.dynamodb_region = os.getenv('DYNAMODB_REGION', 'us-east-1')
        self.dynamodb_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.dynamodb_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.projects_table = os.getenv('DYNAMODB_PROJECTS_TABLE', 'voice_stream_projects')
        self.annotations_table = os.getenv('DYNAMODB_ANNOTATIONS_TABLE', 'voice_stream_annotations')

        # Initialize database client
        self.dynamodb_client = None
        self.dynamodb_resource = None

        if self.db_mode == 'dynamodb':
            self._initialize_dynamodb_client()
        else:
            self._initialize_sqlite_db()

    def _initialize_dynamodb_client(self):
        """Initialize AWS DynamoDB client with error handling"""
        try:
            if self.dynamodb_access_key and self.dynamodb_secret_key:
                self.dynamodb_client = boto3.client(
                    'dynamodb',
                    aws_access_key_id=self.dynamodb_access_key,
                    aws_secret_access_key=self.dynamodb_secret_key,
                    region_name=self.dynamodb_region
                )
                self.dynamodb_resource = boto3.resource(
                    'dynamodb',
                    aws_access_key_id=self.dynamodb_access_key,
                    aws_secret_access_key=self.dynamodb_secret_key,
                    region_name=self.dynamodb_region
                )
            else:
                # Use default credentials (IAM role, environment, or ~/.aws/credentials)
                self.dynamodb_client = boto3.client('dynamodb', region_name=self.dynamodb_region)
                self.dynamodb_resource = boto3.resource('dynamodb', region_name=self.dynamodb_region)

            # Test DynamoDB connection and create tables if needed
            self._setup_dynamodb_tables()
            logger.info(f"✅ DynamoDB client initialized successfully in region: {self.dynamodb_region}")

        except NoCredentialsError:
            logger.error("❌ AWS credentials not found. Falling back to SQLite.")
            self.db_mode = 'sqlite'
            self._initialize_sqlite_db()
        except Exception as e:
            logger.error(f"❌ Failed to initialize DynamoDB client: {str(e)}. Falling back to SQLite.")
            self.db_mode = 'sqlite'
            self._initialize_sqlite_db()

    def _setup_dynamodb_tables(self):
        """Create DynamoDB tables if they don't exist"""
        try:
            # Create Projects table
            try:
                self.dynamodb_client.describe_table(TableName=self.projects_table)
                logger.info(f"✅ Projects table '{self.projects_table}' already exists")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    logger.info(f"📝 Creating projects table: {self.projects_table}")
                    self.dynamodb_client.create_table(
                        TableName=self.projects_table,
                        KeySchema=[
                            {'AttributeName': 'id', 'KeyType': 'HASH'}
                        ],
                        AttributeDefinitions=[
                            {'AttributeName': 'id', 'AttributeType': 'S'}
                        ],
                        BillingMode='PAY_PER_REQUEST'
                    )
                    # Wait for table to be created
                    waiter = self.dynamodb_client.get_waiter('table_exists')
                    waiter.wait(TableName=self.projects_table, WaiterConfig={'Delay': 2, 'MaxAttempts': 30})
                    logger.info(f"✅ Projects table created successfully")
                else:
                    raise e

            # Create Annotations table
            try:
                self.dynamodb_client.describe_table(TableName=self.annotations_table)
                logger.info(f"✅ Annotations table '{self.annotations_table}' already exists")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    logger.info(f"📝 Creating annotations table: {self.annotations_table}")
                    self.dynamodb_client.create_table(
                        TableName=self.annotations_table,
                        KeySchema=[
                            {'AttributeName': 'id', 'KeyType': 'HASH'}
                        ],
                        AttributeDefinitions=[
                            {'AttributeName': 'id', 'AttributeType': 'S'},
                            {'AttributeName': 'project_id', 'AttributeType': 'S'}
                        ],
                        GlobalSecondaryIndexes=[
                            {
                                'IndexName': 'project_id-index',
                                'KeySchema': [
                                    {'AttributeName': 'project_id', 'KeyType': 'HASH'}
                                ],
                                'Projection': {'ProjectionType': 'ALL'}
                            }
                        ],
                        BillingMode='PAY_PER_REQUEST'
                    )
                    # Wait for table to be created
                    waiter = self.dynamodb_client.get_waiter('table_exists')
                    waiter.wait(TableName=self.annotations_table, WaiterConfig={'Delay': 2, 'MaxAttempts': 30})
                    logger.info(f"✅ Annotations table created successfully")
                else:
                    raise e

        except Exception as e:
            logger.error(f"❌ Failed to setup DynamoDB tables: {str(e)}")
            raise e

    def _initialize_sqlite_db(self):
        """Initialize SQLite database with required tables"""
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    workspace_path TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS annotations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    audio_filename TEXT NOT NULL,
                    audio_path TEXT NOT NULL,
                    transcript TEXT NOT NULL,
                    original_transcript TEXT,
                    recording_mode TEXT NOT NULL,
                    language TEXT DEFAULT 'en',
                    duration REAL,
                    deleted TEXT DEFAULT 'N',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            ''')

            # Add deleted column if it doesn't exist
            try:
                conn.execute('ALTER TABLE annotations ADD COLUMN deleted TEXT DEFAULT "N"')
                conn.commit()
            except sqlite3.OperationalError:
                pass  # Column already exists

            conn.commit()
            conn.close()
            logger.info(f"✅ SQLite database initialized: {self.sqlite_db_path}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize SQLite database: {str(e)}")
            raise e

    # Project Management Methods
    def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects with annotation counts"""
        if self.db_mode == 'dynamodb':
            return self._get_projects_dynamodb()
        else:
            return self._get_projects_sqlite()

    def create_project(self, project_name: str, description: str, workspace_path: str) -> str:
        """Create a new project"""
        if self.db_mode == 'dynamodb':
            return self._create_project_dynamodb(project_name, description, workspace_path)
        else:
            return self._create_project_sqlite(project_name, description, workspace_path)

    def get_project_annotations(self, project_id: str) -> List[Dict[str, Any]]:
        """Get annotations for a specific project"""
        if self.db_mode == 'dynamodb':
            return self._get_project_annotations_dynamodb(project_id)
        else:
            return self._get_project_annotations_sqlite(project_id)

    def save_annotation(self, project_id: str, audio_filename: str, audio_path: str,
                       transcript: str, recording_mode: str, language: str, duration: float) -> str:
        """Save a new annotation"""
        if self.db_mode == 'dynamodb':
            return self._save_annotation_dynamodb(project_id, audio_filename, audio_path,
                                                transcript, recording_mode, language, duration)
        else:
            return self._save_annotation_sqlite(project_id, audio_filename, audio_path,
                                              transcript, recording_mode, language, duration)

    def update_transcript(self, annotation_id: str, transcript: str) -> bool:
        """Update annotation transcript"""
        if self.db_mode == 'dynamodb':
            return self._update_transcript_dynamodb(annotation_id, transcript)
        else:
            return self._update_transcript_sqlite(annotation_id, transcript)

    def delete_annotation(self, annotation_id: str) -> bool:
        """Soft delete an annotation"""
        if self.db_mode == 'dynamodb':
            return self._delete_annotation_dynamodb(annotation_id)
        else:
            return self._delete_annotation_sqlite(annotation_id)

    def get_annotation_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get annotation by audio filename"""
        if self.db_mode == 'dynamodb':
            return self._get_annotation_by_filename_dynamodb(filename)
        else:
            return self._get_annotation_by_filename_sqlite(filename)

    # SQLite Implementation Methods
    def _get_projects_sqlite(self) -> List[Dict[str, Any]]:
        """SQLite implementation of get_projects"""
        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.id, p.project_name, p.description, p.workspace_path, p.created_at,
                   COUNT(CASE WHEN a.deleted IS NULL OR a.deleted = 'N' THEN a.id END) as annotation_count
            FROM projects p
            LEFT JOIN annotations a ON p.id = a.project_id
            GROUP BY p.id, p.project_name, p.description, p.workspace_path, p.created_at
            ORDER BY p.created_at DESC
        ''')
        projects = []
        for row in cursor.fetchall():
            projects.append({
                'id': str(row[0]),
                'project_name': row[1],
                'description': row[2],
                'workspace_path': row[3],
                'created_at': row[4],
                'annotation_count': row[5]
            })
        conn.close()
        return projects

    def _create_project_sqlite(self, project_name: str, description: str, workspace_path: str) -> str:
        """SQLite implementation of create_project"""
        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO projects (project_name, description, workspace_path)
            VALUES (?, ?, ?)
        ''', (project_name, description, workspace_path))
        project_id = str(cursor.lastrowid)
        conn.commit()
        conn.close()
        return project_id

    def _get_project_annotations_sqlite(self, project_id: str) -> List[Dict[str, Any]]:
        """SQLite implementation of get_project_annotations"""
        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, audio_filename, audio_path, transcript, original_transcript, recording_mode,
                   language, duration, created_at, updated_at
            FROM annotations
            WHERE project_id = ? AND (deleted IS NULL OR deleted = 'N')
            ORDER BY created_at DESC
        ''', (int(project_id),))

        annotations = []
        for row in cursor.fetchall():
            annotations.append({
                'id': str(row[0]),
                'audio_filename': row[1],
                'audio_path': row[2],
                'transcript': row[3],
                'original_transcript': row[4] if row[4] else '',
                'recording_mode': row[5],
                'language': row[6] if row[6] else 'en',
                'duration': row[7] if row[7] else 0,
                'created_at': row[8],
                'updated_at': row[9]
            })
        conn.close()
        return annotations

    def _save_annotation_sqlite(self, project_id: str, audio_filename: str, audio_path: str,
                               transcript: str, recording_mode: str, language: str, duration: float) -> str:
        """SQLite implementation of save_annotation"""
        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO annotations (project_id, audio_filename, audio_path, transcript,
                                   original_transcript, recording_mode, language, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (int(project_id), audio_filename, audio_path, transcript, transcript,
              recording_mode, language, duration))
        annotation_id = str(cursor.lastrowid)
        conn.commit()
        conn.close()
        return annotation_id

    def _update_transcript_sqlite(self, annotation_id: str, transcript: str) -> bool:
        """SQLite implementation of update_transcript"""
        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE annotations 
            SET transcript = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (transcript, int(annotation_id)))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def _delete_annotation_sqlite(self, annotation_id: str) -> bool:
        """SQLite implementation of delete_annotation"""
        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE annotations 
            SET deleted = 'Y', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (int(annotation_id),))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def _get_annotation_by_filename_sqlite(self, filename: str) -> Optional[Dict[str, Any]]:
        """SQLite implementation of get_annotation_by_filename"""
        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT audio_path, project_id, id FROM annotations WHERE audio_filename = ?', (filename,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return {
                'audio_path': result[0],
                'project_id': str(result[1]),
                'id': str(result[2])
            }
        return None

    # DynamoDB Implementation Methods
    def _get_projects_dynamodb(self) -> List[Dict[str, Any]]:
        """DynamoDB implementation of get_projects"""
        try:
            projects_table = self.dynamodb_resource.Table(self.projects_table)
            annotations_table = self.dynamodb_resource.Table(self.annotations_table)

            # Get all projects
            response = projects_table.scan()
            projects = []

            for item in response['Items']:
                # Count annotations for this project
                annotation_response = annotations_table.scan(
                    FilterExpression='project_id = :pid AND attribute_not_exists(deleted)',
                    ExpressionAttributeValues={':pid': item['id']}
                )
                annotation_count = annotation_response['Count']

                projects.append({
                    'id': item['id'],
                    'project_name': item['project_name'],
                    'description': item.get('description', ''),
                    'workspace_path': item['workspace_path'],
                    'created_at': item['created_at'],
                    'annotation_count': annotation_count
                })

            # Sort by created_at DESC
            projects.sort(key=lambda x: x['created_at'], reverse=True)
            return projects

        except Exception as e:
            logger.error(f"❌ DynamoDB get_projects failed: {str(e)}")
            raise e

    def _create_project_dynamodb(self, project_name: str, description: str, workspace_path: str) -> str:
        """DynamoDB implementation of create_project"""
        try:
            projects_table = self.dynamodb_resource.Table(self.projects_table)

            # Generate unique project ID
            project_id = f"proj_{int(time.time() * 1000)}"
            created_at = datetime.utcnow().isoformat()

            projects_table.put_item(
                Item={
                    'id': project_id,
                    'project_name': project_name,
                    'description': description,
                    'workspace_path': workspace_path,
                    'created_at': created_at
                },
                ConditionExpression='attribute_not_exists(id)'
            )

            return project_id

        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError('Project name already exists')
            logger.error(f"❌ DynamoDB create_project failed: {str(e)}")
            raise e

    def _get_project_annotations_dynamodb(self, project_id: str) -> List[Dict[str, Any]]:
        """DynamoDB implementation of get_project_annotations"""
        try:
            annotations_table = self.dynamodb_resource.Table(self.annotations_table)

            response = annotations_table.query(
                IndexName='project_id-index',
                KeyConditionExpression='project_id = :pid',
                FilterExpression='attribute_not_exists(deleted)',
                ExpressionAttributeValues={':pid': project_id}
            )

            annotations = []
            for item in response['Items']:
                annotations.append({
                    'id': item['id'],
                    'audio_filename': item['audio_filename'],
                    'audio_path': item['audio_path'],
                    'transcript': item['transcript'],
                    'original_transcript': item.get('original_transcript', ''),
                    'recording_mode': item['recording_mode'],
                    'language': item.get('language', 'en'),
                    'duration': float(item.get('duration', 0)),
                    'created_at': item['created_at'],
                    'updated_at': item.get('updated_at', item['created_at'])
                })

            # Sort by created_at DESC
            annotations.sort(key=lambda x: x['created_at'], reverse=True)
            return annotations

        except Exception as e:
            logger.error(f"❌ DynamoDB get_project_annotations failed: {str(e)}")
            raise e

    def _save_annotation_dynamodb(self, project_id: str, audio_filename: str, audio_path: str,
                                 transcript: str, recording_mode: str, language: str, duration: float) -> str:
        """DynamoDB implementation of save_annotation"""
        try:
            annotations_table = self.dynamodb_resource.Table(self.annotations_table)

            # Generate unique annotation ID
            annotation_id = f"anno_{int(time.time() * 1000)}"
            created_at = datetime.utcnow().isoformat()

            annotations_table.put_item(
                Item={
                    'id': annotation_id,
                    'project_id': project_id,
                    'audio_filename': audio_filename,
                    'audio_path': audio_path,
                    'transcript': transcript,
                    'original_transcript': transcript,
                    'recording_mode': recording_mode,
                    'language': language,
                    'duration': duration,
                    'created_at': created_at,
                    'updated_at': created_at
                }
            )

            return annotation_id

        except Exception as e:
            logger.error(f"❌ DynamoDB save_annotation failed: {str(e)}")
            raise e

    def _update_transcript_dynamodb(self, annotation_id: str, transcript: str) -> bool:
        """DynamoDB implementation of update_transcript"""
        try:
            annotations_table = self.dynamodb_resource.Table(self.annotations_table)
            updated_at = datetime.utcnow().isoformat()

            response = annotations_table.update_item(
                Key={'id': annotation_id},
                UpdateExpression='SET transcript = :transcript, updated_at = :updated_at',
                ExpressionAttributeValues={
                    ':transcript': transcript,
                    ':updated_at': updated_at
                },
                ConditionExpression='attribute_exists(id)',
                ReturnValues='UPDATED_NEW'
            )

            return 'Attributes' in response

        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return False
            logger.error(f"❌ DynamoDB update_transcript failed: {str(e)}")
            raise e

    def _delete_annotation_dynamodb(self, annotation_id: str) -> bool:
        """DynamoDB implementation of delete_annotation"""
        try:
            annotations_table = self.dynamodb_resource.Table(self.annotations_table)
            updated_at = datetime.utcnow().isoformat()

            response = annotations_table.update_item(
                Key={'id': annotation_id},
                UpdateExpression='SET deleted = :deleted, updated_at = :updated_at',
                ExpressionAttributeValues={
                    ':deleted': 'Y',
                    ':updated_at': updated_at
                },
                ConditionExpression='attribute_exists(id)',
                ReturnValues='UPDATED_NEW'
            )

            return 'Attributes' in response

        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return False
            logger.error(f"❌ DynamoDB delete_annotation failed: {str(e)}")
            raise e

    def _get_annotation_by_filename_dynamodb(self, filename: str) -> Optional[Dict[str, Any]]:
        """DynamoDB implementation of get_annotation_by_filename"""
        try:
            annotations_table = self.dynamodb_resource.Table(self.annotations_table)

            response = annotations_table.scan(
                FilterExpression='audio_filename = :filename',
                ExpressionAttributeValues={':filename': filename}
            )

            if response['Items']:
                item = response['Items'][0]
                return {
                    'audio_path': item['audio_path'],
                    'project_id': item['project_id'],
                    'id': item['id']
                }
            return None

        except Exception as e:
            logger.error(f"❌ DynamoDB get_annotation_by_filename failed: {str(e)}")
            raise e

    def get_database_info(self) -> Dict[str, Any]:
        """Get current database configuration info"""
        info = {
            'database_mode': self.db_mode,
            'sqlite_db_path': self.sqlite_db_path if self.db_mode == 'sqlite' else None,
            'dynamodb_region': self.dynamodb_region if self.db_mode == 'dynamodb' else None,
            'projects_table': self.projects_table if self.db_mode == 'dynamodb' else None,
            'annotations_table': self.annotations_table if self.db_mode == 'dynamodb' else None,
            'dynamodb_available': self.dynamodb_client is not None
        }
        return info

# Global database manager instance
database_manager = DatabaseManager()
