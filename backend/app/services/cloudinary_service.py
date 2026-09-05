import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)


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