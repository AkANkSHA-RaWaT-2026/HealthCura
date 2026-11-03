"""Uploads and deletes medical document files on Cloudinary."""

import logging
import os
import re

import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)

# Cloudinary URLs contain a version segment such as "v1793708010/" before the path
VERSION_SEGMENT = re.compile(r"^v\d+/")
UPLOAD_MARKER = "/upload/"


def upload_file_to_cloudinary(file_path: str, folder: str = "healthcura_documents") -> str:
    """
    Uploads a file to Cloudinary and returns its public URL.
    Raises an exception if the upload fails - caller must handle it.
    """
    result = cloudinary.uploader.upload(
        file_path,
        folder=folder,
        resource_type="auto",  # auto-detects image vs pdf vs raw file
    )
    return result["secure_url"]


def get_public_id_from_url(file_url: str) -> str | None:
    """
    Returns the Cloudinary public ID for a stored file URL, or None if the URL
    is not a Cloudinary upload URL. Example:
    .../image/upload/v123/healthcura_documents/abc.pdf -> healthcura_documents/abc
    PDFs are stored with resource type "image", so the extension is dropped.
    """
    if UPLOAD_MARKER not in file_url:
        return None

    path = file_url.split(UPLOAD_MARKER, 1)[1]
    path = VERSION_SEGMENT.sub("", path)
    public_id, _ = os.path.splitext(path)
    return public_id or None


def delete_file_from_cloudinary(file_url: str) -> bool:
    """
    Deletes the file behind a stored URL. Returns True if Cloudinary confirms
    the deletion, False otherwise. Raises an exception if the request itself fails.
    """
    public_id = get_public_id_from_url(file_url)
    if public_id is None:
        logger.warning("Skipping Cloudinary delete: not a Cloudinary URL.")
        return False

    result = cloudinary.uploader.destroy(public_id, resource_type="image", invalidate=True)
    confirmed = result.get("result") == "ok"
    if not confirmed:
        logger.warning("Cloudinary did not confirm delete for %s: %s", public_id, result)
    return confirmed