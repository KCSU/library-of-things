"""Uploaded file handling."""

import logging

from werkzeug.datastructures import FileStorage

from app.config import IMAGE_MAX_UPLOAD_BYTES

logger = logging.getLogger(__name__)


def read_upload(
    file_storage: FileStorage | None, max_bytes: int = IMAGE_MAX_UPLOAD_BYTES
) -> bytes:
    if file_storage is None or not getattr(file_storage, 'filename', ''):
        raise ValueError('No file was uploaded')

    content = file_storage.read(max_bytes + 1)
    if not content:
        raise ValueError('The uploaded file was empty')
    if len(content) > max_bytes:
        raise ValueError(f'File is larger than {max_bytes // (1024 * 1024)}MB')

    logger.info('Accepted upload %r (%d bytes)', file_storage.filename, len(content))
    return content
