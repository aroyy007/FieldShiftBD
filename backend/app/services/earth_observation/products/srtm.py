"""Read one SRTMGL1 HGT grid node without extracting an archive."""
import hashlib
import math
import re
import struct
import zlib
from pathlib import Path
from zipfile import BadZipFile, ZipFile


def sample_hgt(path: Path, latitude: float, longitude: float) -> dict:
    path = Path(path)
    match = re.fullmatch(r'N(\d{2})E(\d{3})\.SRTMGL1\.hgt\.zip', path.name)
    if not match or path.is_symlink() or not path.is_file() or path.stat().st_size > 64*1024*1024:
        raise ValueError('Invalid SRTM archive')
    south, west = map(int, match.groups())
    if not math.isfinite(latitude) or not math.isfinite(longitude) or not (south <= latitude <= south+1 and west <= longitude <= west+1):
        raise ValueError('Point is outside the tile')
    member = f'N{south:02d}E{west:03d}.hgt'
    try:
        with ZipFile(path) as archive:
            entries = archive.infolist()
            if len(entries) != 1 or entries[0].filename != member or entries[0].file_size != 3601*3601*2:
                raise ValueError('Unexpected SRTM archive content')
            data = archive.read(entries[0])
    except (BadZipFile, RuntimeError, NotImplementedError, EOFError, zlib.error) as exc:
        raise ValueError('Invalid SRTM archive') from exc
    row = round((south+1-latitude)*3600)
    col = round((longitude-west)*3600)
    value = struct.unpack_from('>h',data,(row*3601+col)*2)[0]
    return {'latitude':south+1-row/3600,'longitude':west+col/3600,
            'elevation_m':None if value == -32768 else value,
            'source_file':path.name,'checksum_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'acquisition_method':'user_supplied_unverified','acquisition_date':'2000-02',
            'product':'SRTMGL1 V003','native_support':'1 arc-second grid node'}
