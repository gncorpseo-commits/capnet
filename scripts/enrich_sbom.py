"""cyclonedx raw JSON → CapNet 루트 sbom.json 메타 보강."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: enrich_sbom.py <raw.json> <out.json>")
    raw_path, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    bom = json.loads(raw_path.read_text(encoding="utf-8"))
    bom["metadata"] = bom.get("metadata") or {}
    bom["metadata"]["timestamp"] = datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    bom["metadata"]["component"] = {
        "type": "application",
        "name": "CapNet",
        "version": "0.1.0-contest",
        "licenses": [{"license": {"id": "Apache-2.0"}}],
        "purl": "pkg:github/gncorpseo-commits/capnet",
    }
    bom["metadata"]["properties"] = [
        {
            "name": "capnet:sbom:source",
            "value": "scripts/generate_sbom + cyclonedx-py",
        },
        {
            "name": "capnet:sbom:note",
            "value": (
                "torch/torchvision unpinned: "
                "node-m-team Dockerfile pytorch CPU index"
            ),
        },
    ]
    comps = bom.get("components") or []
    if not any(c.get("name") == "postgresql" for c in comps):
        comps.append(
            {
                "type": "container",
                "name": "postgresql",
                "version": "16",
                "purl": "pkg:docker/library/postgres@16",
                "licenses": [{"license": {"name": "PostgreSQL License"}}],
                "description": "compose service postgres:16",
            }
        )
    bom["components"] = comps
    bom["serialNumber"] = f"urn:uuid:{uuid4()}"
    bom["externalReferences"] = [
        {
            "type": "website",
            "url": "https://github.com/gncorpseo-commits/capnet",
        },
        {
            "type": "distribution",
            "url": (
                "https://github.com/gncorpseo-commits/capnet/"
                "blob/main/THIRD-PARTY-LICENSES.md"
            ),
        },
    ]
    out_path.write_text(
        json.dumps(bom, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote {out_path} components={len(comps)}")


if __name__ == "__main__":
    main()
