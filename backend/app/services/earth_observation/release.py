"""Bounded immutable Parquet releases. Publication does not certify agronomy."""
from __future__ import annotations
import hashlib
import io
import json
import os
import re
import tempfile
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from app.services.earth_observation.registry import product_registry, region_registry

MAX_BYTES = 64 * 1024 * 1024
MAX_ROWS = 100_000


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()


def _atomic(path: Path, data: bytes):
    fd, name = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def publish_release(root: Path, metadata: dict, rows: list[dict]) -> str:
    if metadata.get('district_code') not in region_registry():
        raise ValueError('Unsupported region')
    if not metadata.get('products') or set(metadata['products']) - product_registry().keys():
        raise ValueError('Unknown products')
    if metadata.get('scope') not in ('reference_point', 'regional_grid', 'pilot_grid'):
        raise ValueError('Explicit evidence scope is required')
    if not 1 <= len(rows) <= MAX_ROWS:
        raise ValueError('Release row count out of bounds')
    table = pa.Table.from_pylist(rows)
    if table.nbytes > MAX_BYTES:
        raise ValueError('Decoded feature table exceeds limit')
    stream = io.BytesIO()
    pq.write_table(table, stream, compression='zstd')
    data = stream.getvalue()
    if len(data) > MAX_BYTES:
        raise ValueError('Feature file exceeds limit')
    checksum = hashlib.sha256(data).hexdigest()
    manifest = {**metadata, 'format_version': 'eo-features-v1', 'checksum_sha256': checksum, 'rows': len(rows), 'bytes': len(data)}
    digest = hashlib.sha256(_json(manifest)).hexdigest()
    root = root.resolve()
    directory = root / digest
    if directory.is_symlink():
        raise ValueError('Symlink release refused')
    directory.mkdir(parents=True, exist_ok=True)
    if (directory / 'manifest.json').exists():
        read_release(root, digest)
        return digest
    _atomic(directory / 'features.parquet', data)
    _atomic(directory / 'manifest.json', _json(manifest))
    return digest


def read_release(root: Path, release_id: str) -> dict:
    if not re.fullmatch(r'[a-f0-9]{64}', release_id):
        raise ValueError('Invalid release ID')
    directory = root.resolve() / release_id
    if directory.is_symlink():
        raise ValueError('Symlink release refused')
    manifest_path, data_path = directory / 'manifest.json', directory / 'features.parquet'
    for path, limit in ((manifest_path, 1024 * 1024), (data_path, MAX_BYTES)):
        if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
            raise ValueError('Release file is missing, unsafe or oversized')
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw)
    if hashlib.sha256(_json(manifest)).hexdigest() != release_id:
        raise ValueError('Manifest checksum mismatch')
    data = data_path.read_bytes()
    if hashlib.sha256(data).hexdigest() != manifest['checksum_sha256']:
        raise ValueError('Feature checksum mismatch')
    parquet = pq.ParquetFile(io.BytesIO(data), thrift_string_size_limit=MAX_BYTES, thrift_container_size_limit=MAX_ROWS)
    if not 1 <= parquet.metadata.num_rows <= MAX_ROWS or parquet.metadata.num_rows != manifest['rows'] or parquet.metadata.num_row_groups > 100:
        raise ValueError('Feature row count mismatch')
    if sum(parquet.metadata.row_group(i).total_byte_size for i in range(parquet.metadata.num_row_groups)) > MAX_BYTES:
        raise ValueError('Decoded feature limit exceeded')
    return {'release_id': release_id, 'metadata': manifest, 'rows': parquet.read().to_pylist()}
