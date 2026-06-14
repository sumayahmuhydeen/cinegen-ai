"""
Cloudflare R2 Storage Integration
====================================
Handles all media file storage — clips, audio, bibles, exports.
Same S3 API as AWS but with free egress — significant cost saving at scale.
"""
import logging
import os
from core.config import settings

logger = logging.getLogger(__name__)

class R2StorageClient:
    def __init__(self):
        self.mock_mode = not bool(settings.CLOUDFLARE_R2_ACCESS_KEY)
        if self.mock_mode:
            logger.warning("R2 credentials not set — using mock storage")

    async def upload_file(
        self,
        file_bytes: bytes,
        key: str,
        content_type: str = "video/mp4"
    ) -> str:
        """Upload file to R2, return public URL."""
        if self.mock_mode:
            logger.info(f"[MOCK] R2 upload: {key} ({len(file_bytes)} bytes)")
            return f"https://mock-storage.cinegen.ai/{key}"

        try:
            import boto3
            s3 = boto3.client(
                "s3",
                endpoint_url=settings.CLOUDFLARE_R2_ENDPOINT,
                aws_access_key_id=settings.CLOUDFLARE_R2_ACCESS_KEY,
                aws_secret_access_key=settings.CLOUDFLARE_R2_SECRET_KEY,
            )
            s3.put_object(
                Bucket=settings.CLOUDFLARE_R2_BUCKET,
                Key=key,
                Body=file_bytes,
                ContentType=content_type,
            )
            return f"{settings.CLOUDFLARE_R2_ENDPOINT}/{settings.CLOUDFLARE_R2_BUCKET}/{key}"
        except Exception as e:
            logger.error(f"R2 upload failed for {key}: {e}")
            raise

    def get_project_prefix(self, project_id: str) -> str:
        return f"projects/{project_id}"

    def shot_video_key(self, project_id: str, shot_id: str) -> str:
        return f"projects/{project_id}/shots/{shot_id}/video.mp4"

    def shot_audio_key(self, project_id: str, shot_id: str) -> str:
        return f"projects/{project_id}/shots/{shot_id}/audio.mp3"

    def scene_music_key(self, project_id: str, scene_id: str) -> str:
        return f"projects/{project_id}/scenes/{scene_id}/music.mp3"

    def export_key(self, project_id: str, export_id: str) -> str:
        return f"projects/{project_id}/exports/{export_id}/final.mp4"

r2_storage = R2StorageClient()
