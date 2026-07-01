import base64
import os
import uuid
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError
from cryptography.fernet import Fernet

from app.config import settings


class StorageService:
    def __init__(self):
        self.s3 = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )
        self.bucket = settings.s3_bucket_name
        self._ensure_bucket()
        # file_encryption_key must be a base64 encoded 32-byte key
        self.fernet = Fernet(settings.file_encryption_key.encode())

    def _ensure_bucket(self):
        try:
            self.s3.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            error_code = int(e.response["Error"]["Code"])
            if error_code == 404:
                self.s3.create_bucket(Bucket=self.bucket)
            else:
                raise

    def upload_encrypted(self, file_obj: BinaryIO, filename: str) -> str:
        # Read the file
        data = file_obj.read()
        # Encrypt the data
        encrypted_data = self.fernet.encrypt(data)
        # Generate a unique key
        key = f"uploads/{uuid.uuid4()}/{filename}"
        # Upload
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=encrypted_data)
        return key

    def download_decrypted(self, key: str, output_path: str):
        response = self.s3.get_object(Bucket=self.bucket, Key=key)
        encrypted_data = response["Body"].read()
        data = self.fernet.decrypt(encrypted_data)
        with open(output_path, "wb") as f:
            f.write(data)

    def delete_file(self, key: str):
        self.s3.delete_object(Bucket=self.bucket, Key=key)

storage_service = StorageService()
