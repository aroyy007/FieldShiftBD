"""Match a user-downloaded IMERG granule to a CMR report and prepare it for QA."""
import argparse
import json
from pathlib import Path

from app.services.earth_observation.manual_import import import_imerg_granule


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-report', type=Path, required=True)
    parser.add_argument('--granule-id', required=True)
    parser.add_argument('--file', type=Path, required=True)
    parser.add_argument('--output-report', type=Path, required=True)
    parser.add_argument('--raw-dir', type=Path, default=Path('data/earth_observation/raw'))
    args = parser.parse_args()
    try:
        if args.source_report.stat().st_size > 4 * 1024 * 1024:
            raise ValueError('Report too large')
        if args.output_report.resolve() == args.source_report.resolve():
            raise ValueError('Output report must be separate from the discovery report')
        report = import_imerg_granule(json.loads(args.source_report.read_text()), args.granule_id, args.file, args.raw_dir)
        args.output_report.parent.mkdir(parents=True, exist_ok=True)
        args.output_report.write_text(json.dumps(report, indent=2) + '\n')
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(2, f'Import failed: {type(exc).__name__}; check filename, source report, and data format.\n')
    print('Imported user-supplied asset for QA only; not verified or activated.')


if __name__ == '__main__':
    main()
