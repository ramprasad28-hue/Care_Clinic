"""Cloudinary-backed storage for Care_Clinic uploaded images."""

import os
import posixpath
from pathlib import PurePosixPath
from urllib.request import urlopen

import cloudinary
from cloudinary import uploader
from cloudinary.utils import cloudinary_url

from django.core.exceptions import ImproperlyConfigured, SuspiciousFileOperation
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.core.files.utils import validate_file_name


class CloudinaryMediaStorage(Storage):
    """Store clinic images in Cloudinary."""

    asset_folder = "care-clinic"

    def _configure(self):
        cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", "").strip()
        api_key = os.environ.get("CLOUDINARY_API_KEY", "").strip()
        api_secret = os.environ.get("CLOUDINARY_API_SECRET", "").strip()

        if not all((cloud_name, api_key, api_secret)):
            raise ImproperlyConfigured(
                "Set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, "
                "and CLOUDINARY_API_SECRET in the environment."
            )

        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
        )

    @staticmethod
    def _normalize_name(name):
        name = str(name).replace("\\", "/")
        normalized = posixpath.normpath(name)

        if (
            name.startswith("/")
            or normalized in ("", ".", "..")
            or normalized.startswith("../")
        ):
            raise SuspiciousFileOperation(
                "Invalid uploaded image path."
            )

        return validate_file_name(
            normalized,
            allow_relative_path=True,
        )

    def _public_id(self, name):
        normalized = self._normalize_name(name)
        path = PurePosixPath(normalized)

        # Keep the public ID extensionless, as expected for image uploads.
        relative_path = path.with_suffix("")

        prefix = f"{self.asset_folder}/"

        if str(relative_path).startswith(prefix):
            return str(relative_path)

        return f"{self.asset_folder}/{relative_path}"

    def get_available_name(self, name, max_length=None):
        # Use stable names and overwrite the corresponding Cloudinary asset
        # when an administrator replaces an image.
        name = self._normalize_name(name)

        if max_length is not None and len(name) > max_length:
            raise SuspiciousFileOperation(
                "The uploaded image path exceeds the allowed length."
            )

        return name

    def _save(self, name, content):
        self._configure()

        name = self._normalize_name(name)
        public_id = self._public_id(name)

        if hasattr(content, "seek"):
            content.seek(0)

        uploader.upload(
            content,
            public_id=public_id,
            resource_type="image",
            overwrite=True,
            invalidate=True,
            asset_folder=self.asset_folder,
            use_asset_folder_as_public_id_prefix=False,
        )

        # Store the relative image name in the existing Django ImageField.
        return name

    def _open(self, name, mode="rb"):
        if mode not in ("rb", "r"):
            raise ValueError(
                "Cloudinary storage supports read-only access."
            )

        with urlopen(self.url(name), timeout=20) as response:
            content = response.read()

        return ContentFile(content, name=name)

    def url(self, name):
        self._configure()

        normalized = self._normalize_name(name)
        public_id = self._public_id(normalized)

        extension = PurePosixPath(normalized).suffix.lstrip(".")

        url, _ = cloudinary_url(
            public_id,
            resource_type="image",
            secure=True,
            format=extension or None,
        )

        return url

    def delete(self, name):
        self._configure()

        uploader.destroy(
            self._public_id(name),
            resource_type="image",
            invalidate=True,
        )