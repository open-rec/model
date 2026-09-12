#!/usr/bin/env python3
"""Publish the canonical catalog into self-contained consumer source trees."""

import argparse
import hashlib
import shutil
from pathlib import Path


HERE = Path(__file__).resolve().parent
CATALOG = HERE / "feature.catalog.json"
PARITY_FIXTURE = HERE / "event-feature-parity.json"
WORKSPACE = HERE.parents[2]
TARGETS = (
    WORKSPACE / "rec-algorithm/algorithm/feature/definitions/feature.catalog.json",
    WORKSPACE / "data-processor/feature-core/src/main/resources/openrec-feature-catalog.json",
)
FIXTURE_TARGETS = (
    WORKSPACE / "rec-algorithm/algorithm/feature/definitions/event-feature-parity.json",
    WORKSPACE / "data-processor/feature-core/src/test/resources/event-feature-parity.json",
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = digest(CATALOG)
    stale = [path for path in TARGETS if not path.exists() or digest(path) != expected]
    stale += [path for path in FIXTURE_TARGETS
              if not path.exists() or digest(path) != digest(PARITY_FIXTURE)]
    if args.check:
        if stale:
            raise SystemExit("stale feature catalog copies: " + ", ".join(map(str, stale)))
    else:
        for path in TARGETS:
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(CATALOG, path)
        for path in FIXTURE_TARGETS:
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PARITY_FIXTURE, path)
    print("catalog_version=2 catalog_sha256=" + expected)


if __name__ == "__main__":
    main()
