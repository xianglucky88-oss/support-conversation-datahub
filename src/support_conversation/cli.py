from __future__ import annotations

import argparse
import json

from .pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--database", required=True)
    args = parser.parse_args()
    with open(args.fixture, encoding="utf-8") as handle:
        print(json.dumps(run_pipeline(json.load(handle), args.database), sort_keys=True))


if __name__ == "__main__":
    main()
