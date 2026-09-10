#!/usr/bin/env python3
"""Validate the canonical catalog without third-party dependencies."""

import json
import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = Path(__file__).with_name("feature.catalog.json")
ID_PATTERN = re.compile(r"^(user|item|context|cross)\.[a-z][a-z0-9_]*$")
REQUIRED = {
    "id", "definition_version", "entity", "group", "name", "description",
    "value_type", "shape", "source", "default", "materialization", "status",
}


def fail(message):
    raise SystemExit("feature catalog validation failed: " + message)


def main():
    catalog = json.loads(CATALOG_PATH.read_text())
    catalog_sha256 = hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest()
    if catalog.get("schema_version") != 1:
        fail("unsupported schema_version")
    if not isinstance(catalog.get("catalog_version"), int) or catalog["catalog_version"] < 1:
        fail("catalog_version must be a positive integer")
    policies = catalog.get("policies")
    features = catalog.get("features")
    if not isinstance(policies, dict) or not policies:
        fail("policies must be a non-empty object")
    if not isinstance(features, list) or not features:
        fail("features must be a non-empty array")

    feature_ids = set()
    for index, feature in enumerate(features):
        missing = REQUIRED - set(feature)
        if missing:
            fail("feature %d misses %s" % (index, sorted(missing)))
        feature_id = feature["id"]
        if not ID_PATTERN.match(feature_id):
            fail("invalid feature id: " + str(feature_id))
        if feature_id in feature_ids:
            fail("duplicate feature id: " + feature_id)
        feature_ids.add(feature_id)
        entity, name = feature_id.split(".", 1)
        if feature["entity"] != entity or feature["name"] != name:
            fail("id/entity/name disagree for " + feature_id)
        if feature.get("policy") not in policies:
            fail("unknown policy for " + feature_id)
        materialization = feature["materialization"]
        if set(materialization) != {"online", "offline", "backfillable"}:
            fail("invalid materialization for " + feature_id)
        if not all(isinstance(value, bool) for value in materialization.values()):
            fail("materialization flags must be boolean for " + feature_id)
        if feature["group"] == "behavior" and "aggregation" not in feature:
            fail("behavior feature lacks aggregation: " + feature_id)

    referenced = set()
    for path in (ROOT / "rank").glob("*/*.features.json"):
        sidecar = json.loads(path.read_text())
        for section in ("user", "item"):
            for column in sidecar.get(section, []):
                feature_id = column.get("feature")
                if not feature_id:
                    fail("%s has an unregistered %s column" % (path.relative_to(ROOT), section))
                referenced.add(feature_id)
        if sidecar.get("catalog_version") != catalog["catalog_version"]:
            fail("%s uses catalog_version %s, expected %s" % (
                path.relative_to(ROOT), sidecar.get("catalog_version"),
                catalog["catalog_version"]))
        if sidecar.get("catalog_sha256") != catalog_sha256:
            fail("%s uses a missing or different catalog_sha256" % path.relative_to(ROOT))
        manifest_path = path.with_name(path.name.replace(".features.json", ".manifest.json"))
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            for field, expected in (("catalog_version", catalog["catalog_version"]),
                                    ("catalog_sha256", catalog_sha256)):
                if manifest.get(field) != expected:
                    fail("%s uses a missing or different %s" % (
                        manifest_path.relative_to(ROOT), field))
    missing = sorted(referenced - feature_ids)
    if missing:
        fail("model sidecars reference unknown features: " + ", ".join(missing))

    print("validated %d canonical features and %d fitted feature references" % (
        len(feature_ids), len(referenced)))


if __name__ == "__main__":
    main()
