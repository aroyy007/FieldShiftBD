"""Import a user-downloaded pilot IMERG file against a CMR discovery report.

Filename and hash checks do not authenticate the upstream download. The file
and district label remain unverified until product and provenance review.
"""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from urllib.parse import unquote, urlparse
import os
import tempfile

from app.services.earth_observation.acquisition import _official
from app.services.earth_observation.products.imerg import MAX_FILE_BYTES


def import_imerg_granule(report: dict, granule_id: str, source: Path, raw_root: Path) -> dict:
    result = deepcopy(report)
    matches = [x for x in result.get('results', []) if x.get('product_id') == 'imerg']
    if len(matches) != 1:
        raise ValueError('Exactly one IMERG discovery record is required')
    record = matches[0]
    if record.get('query', {}).get('short_name') != 'GPM_3IMERGDF' or record.get('query', {}).get('version') != '07':
        raise ValueError('Unsupported IMERG product')
    assets = [a for a in record.get('assets', []) if a.get('granule_id') == granule_id]
    if len(assets) != 1 or not assets[0].get('start'):
        raise ValueError('Granule not uniquely identified in discovery report')
    asset = assets[0]
    names = set()
    for url in asset.get('download_urls', []):
        _official(url)
        names.add(Path(unquote(urlparse(url).path)).name)
    source = Path(source)
    if source.name not in names:
        raise ValueError('Downloaded filename does not match the discovered granule')
    if source.is_symlink() or not source.is_file() or not 0 < source.stat().st_size <= MAX_FILE_BYTES:
        raise ValueError('Invalid or oversized IMERG file')
    raw_root.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix='.manual-', dir=raw_root)
    try:
        digest = sha256()
        size = 0
        with os.fdopen(fd, 'wb') as output, source.open('rb') as incoming:
            header = incoming.read(8)
            if header != b'\x89HDF\r\n\x1a\n':
                raise ValueError('Expected HDF5/NetCDF4 data, not a login/error page')
            digest.update(header); output.write(header); size = len(header)
            for chunk in iter(lambda: incoming.read(1024 * 1024), b''):
                size += len(chunk)
                if size > MAX_FILE_BYTES:
                    raise ValueError('File exceeds IMERG worker byte limit')
                digest.update(chunk); output.write(chunk)
            output.flush(); os.fsync(output.fileno())
        checksum = digest.hexdigest()
        target = raw_root / checksum
        if target.is_symlink() or (target.exists() and sha256(target.read_bytes()).hexdigest() != checksum):
            raise ValueError('Existing asset checksum mismatch')
        os.replace(temp, target)
        record['sample'] = {'state':'downloaded_pending_product_qa', 'acquisition_method':'user_supplied_unverified',
            'checksum_sha256':checksum, 'bytes':size, 'relative_path':checksum,
            'granule_id':granule_id, 'observation_start':asset['start']}
        return result
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
