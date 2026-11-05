"""Stage a downloaded IMERG pilot for review; never activate it as current evidence."""
import argparse
import json
from pathlib import Path
from app.services.earth_observation.ingestion import stage_imerg_sample


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-report',type=Path,required=True)
    parser.add_argument('--raw-dir',type=Path,default=Path('data/earth_observation/raw'))
    parser.add_argument('--release-dir',type=Path,default=Path('data/earth_observation/staged'))
    args=parser.parse_args()
    if args.source_report.stat().st_size > 4*1024*1024:
        parser.error('Source report exceeds metadata limit')
    try:
        result=stage_imerg_sample(json.loads(args.source_report.read_text()),args.raw_dir,args.release_dir)
    except (ValueError,KeyError,OSError) as error:
        parser.exit(2,f'IMERG sample was not staged: {type(error).__name__}. Verify completed download, units, date, dimensions and source report.\n')
    print(json.dumps(result))


if __name__=='__main__':
    main()
