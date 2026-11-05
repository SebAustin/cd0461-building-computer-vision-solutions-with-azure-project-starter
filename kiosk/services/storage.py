"""Azure Blob Storage: one container per kind of input/output (docs/validation-rules.md)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient, ContainerClient

from kiosk.config import setting

log = logging.getLogger(__name__)

CONTAINERS = (
    "manifest",
    "digital-ids",
    "boarding-passes",
    "training-boarding-passes",
    "identity-videos",
    "luggage-scans",
    "kiosk-results",
)


def service_client() -> BlobServiceClient:
    return BlobServiceClient.from_connection_string(setting("AZURE_STORAGE_CONNECTION_STRING"))


def ensure_containers(client: BlobServiceClient) -> list[str]:
    created = []
    for name in CONTAINERS:
        try:
            client.create_container(name)
            created.append(name)
        except ResourceExistsError:
            pass
    return created


def container(client: BlobServiceClient, name: str) -> ContainerClient:
    if name not in CONTAINERS:
        raise ValueError(f"unknown container {name!r}; expected one of {CONTAINERS}")
    return client.get_container_client(name)


def upload_file(client: BlobServiceClient, container_name: str, path: Path, blob_name: str | None = None) -> str:
    blob = blob_name or path.name
    with path.open("rb") as handle:
        container(client, container_name).upload_blob(blob, handle, overwrite=True)
    log.info("uploaded %s -> %s/%s", path.name, container_name, blob)
    return blob


def upload_json(client: BlobServiceClient, container_name: str, blob_name: str, payload: object) -> str:
    data = json.dumps(payload, indent=2, default=str).encode()
    container(client, container_name).upload_blob(blob_name, data, overwrite=True)
    return blob_name


def list_blobs(client: BlobServiceClient, container_name: str) -> list[str]:
    return [b.name for b in container(client, container_name).list_blobs()]
