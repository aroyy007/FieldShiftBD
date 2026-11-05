import hashlib
from pathlib import Path

import pytest

from app.services.earth_observation.manual_import import import_imerg_granule


def report():
    return {'district_code':'5081','bbox':[88.5,24,88.7,24.2], 'results':[{
        'product_id':'imerg','query':{'short_name':'GPM_3IMERGDF','version':'07','bounding_box':'88.5,24,88.7,24.2'},
        'assets':[{'granule_id':'G-TEST','start':'2024-01-01T00:00:00Z',
                   'download_urls':['https://gpm1.gesdisc.eosdis.nasa.gov/data/sample.nc4']}]}]}


def test_manual_import_keeps_source_identity_and_unverified_status(tmp_path):
    source = tmp_path/'sample.nc4'
    content = b'\x89HDF\r\n\x1a\n' + b'synthetic fixture'
    source.write_bytes(content)
    result = import_imerg_granule(report(), 'G-TEST', source, tmp_path/'raw')
    sample = result['results'][0]['sample']
    assert sample['checksum_sha256'] == hashlib.sha256(content).hexdigest()
    assert sample['acquisition_method'] == 'user_supplied_unverified'
    assert (tmp_path/'raw'/sample['relative_path']).read_bytes() == content
    assert 'sample' not in report()['results'][0]


def test_manual_import_rejects_wrong_file_name_and_html(tmp_path):
    path = tmp_path/'wrong.nc4'; path.write_bytes(b'\x89HDF\r\n\x1a\n')
    with pytest.raises(ValueError, match='filename'):
        import_imerg_granule(report(), 'G-TEST', path, tmp_path/'raw')
    path = tmp_path/'sample.nc4'; path.write_bytes(b'<html>Login required</html>')
    with pytest.raises(ValueError, match='HDF'):
        import_imerg_granule(report(), 'G-TEST', path, tmp_path/'raw')


def test_manual_import_rejects_unlisted_granule(tmp_path):
    path = tmp_path/'sample.nc4'; path.write_bytes(b'\x89HDF\r\n\x1a\n')
    with pytest.raises(ValueError, match='[Gg]ranule'):
        import_imerg_granule(report(), 'G-OTHER', path, tmp_path/'raw')
