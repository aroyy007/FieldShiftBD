from pathlib import Path
from zipfile import ZipFile

import pytest

from app.services.earth_observation.products.srtm import sample_hgt


def test_srtm_native_hgt_reference_point_and_void(tmp_path):
    path = tmp_path/'N24E088.SRTMGL1.hgt.zip'
    data = bytearray(3601*3601*2)
    position = (1800*3601+1800)*2
    data[position:position+2] = (37).to_bytes(2, 'big', signed=True)
    asymmetric = (2700*3601+900)*2
    data[asymmetric:asymmetric+2] = (123).to_bytes(2,'big',signed=True)
    with ZipFile(path,'w') as z:
        z.writestr('N24E088.hgt',data)
    result = sample_hgt(path, 24.5, 88.5)
    assert result['elevation_m'] == 37 and result['latitude'] == 24.5
    assert result['acquisition_method'] == 'user_supplied_unverified'
    assert sample_hgt(path,24.25,88.25)['elevation_m'] == 123
    from app.services.earth_observation.pilot import read_pilot_terrain
    raw = tmp_path/'raw'; raw.mkdir(); path.rename(raw/path.name)
    field_sample = read_pilot_terrain(tmp_path,'5081',24.5,88.5)
    assert field_sample['elevation_m'] == 37
    assert field_sample['sample_basis'] == 'field_profile_coordinate'
    (raw/path.name).write_bytes(b'tampered')
    assert read_pilot_terrain(tmp_path,'5081',24.5,88.5) is None
    data[position:position+2] = (-32768).to_bytes(2,'big',signed=True)
    with ZipFile(path,'w') as z:
        z.writestr('N24E088.hgt',data)
    assert sample_hgt(path,24.5,88.5)['elevation_m'] is None
    with pytest.raises(ValueError,match='outside'):
        sample_hgt(path,25.5,88.5)


def test_srtm_rejects_incorrect_archive_member(tmp_path):
    path = tmp_path/'N24E088.SRTMGL1.hgt.zip'
    with ZipFile(path,'w') as z:
        z.writestr('../escape', b'x')
    with pytest.raises(ValueError,match='archive'):
        sample_hgt(path,24.5,88.5)


def test_srtm_unreadable_archive_is_a_validation_error(tmp_path, monkeypatch):
    path = tmp_path/'N24E088.SRTMGL1.hgt.zip'
    with ZipFile(path,'w') as z:
        z.writestr('N24E088.hgt', bytes(3601*3601*2))
    def cannot_read(*args, **kwargs):
        raise RuntimeError('encrypted archive')
    monkeypatch.setattr(ZipFile,'read',cannot_read)
    with pytest.raises(ValueError,match='archive'):
        sample_hgt(path,24.5,88.5)


def test_rotation_terrain_uses_farmland_coordinate_instead_of_static_city_point(tmp_path):
    from app.services.earth_observation.pilot import read_pilot_terrain

    raw = tmp_path / 'raw'
    raw.mkdir()
    path = raw / 'N24E088.SRTMGL1.hgt.zip'
    data = bytearray(3601 * 3601 * 2)
    row = round((25 - 24.4) * 3600)
    col = round((88.7 - 88) * 3600)
    data[(row * 3601 + col) * 2:(row * 3601 + col) * 2 + 2] = (52).to_bytes(2, 'big', signed=True)
    with ZipFile(path, 'w') as archive:
        archive.writestr('N24E088.hgt', data)

    result = read_pilot_terrain(tmp_path, '5081', 24.4, 88.7)

    assert result['elevation_m'] == 52
    assert result['sample_basis'] == 'field_profile_coordinate'
    assert (result['latitude'], result['longitude']) == pytest.approx((24.4, 88.7), abs=1 / 3600)


def test_rotation_terrain_is_absent_when_field_coordinate_is_outside_available_tile(tmp_path):
    from app.services.earth_observation.pilot import read_pilot_terrain

    assert read_pilot_terrain(tmp_path, '5081', 23.9, 88.7) is None
