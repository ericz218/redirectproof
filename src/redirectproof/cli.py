import argparse
import json
from pathlib import Path

from . import __version__
from .check import check


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Detect redirect mistakes before deploy.")
    parser.add_argument("path", nargs="?", default=".", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args(argv)
    findings = check(args.path.resolve())
    if args.json:
        print(json.dumps([item.as_dict() for item in findings], indent=2))
    elif findings:
        for item in findings:
            print(f"ERROR {item.rule} {item.location}: {item.message}")
    else:
        print(f"PASS {args.path}")
    return bool(findings)


if __name__ == "__main__":
    raise SystemExit(main())
