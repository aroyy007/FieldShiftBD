"""Prepare two labelled reference points from locally downloaded SRTM tiles."""
import json
from pathlib import Path

from app.services.earth_observation.products.srtm import sample_hgt


def main():
    root = Path('data/earth_observation')
    samples = {
        '5081':sample_hgt(root/'raw/N24E088.SRTMGL1.hgt.zip',24.35,88.65),
        '2015':sample_hgt(root/'raw/N22E091.SRTMGL1.hgt.zip',22.35,91.75),
    }
    (root/'pilot-terrain.json').write_text(json.dumps(samples,indent=2)+'\n')
    print('Prepared unverified 2000 SRTM reference points for prototype only.')


if __name__ == '__main__':
    main()
