import boto3
from botocore.exceptions import ClientError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class S3Service:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        self.bucket = settings.AWS_BUCKET

    def upload_file(self, file_path: str, s3_key: str) -> dict:
        try:
            self.client.upload_file(file_path, self.bucket, s3_key)
            return {"status": "success", "key": s3_key}
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            return {"status": "failed", "error": str(e)}

    def read_file(self, s3_key: str) -> bytes | None:
        try:
            obj = self.client.get_object(Bucket=self.bucket, Key=s3_key)
            return obj["Body"].read()
        except ClientError as e:
            logger.error(f"S3 read error: {e}")
            return None

    def delete_file(self, s3_key: str) -> dict:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=s3_key)
            return {"status": "success"}
        except ClientError as e:
            logger.error(f"S3 delete error: {e}")
            return {"status": "failed", "error": str(e)}

    def get_presigned_url(self, s3_key: str, expiry: int = 3600) -> str | None:
        try:
            return self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": s3_key},
                ExpiresIn=expiry,
            )
        except ClientError as e:
            logger.error(f"S3 presigned URL error: {e}")
            return None


s3_service = S3Service()
