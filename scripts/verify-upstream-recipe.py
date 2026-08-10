#!/usr/bin/env python3
"""Verify Hugo's multi-platform image benchmark plan."""

import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ["docker", "buildx", "build", "--file", "upstream/Dockerfile", "--platform", "linux/amd64,linux/arm64", "--build-arg", "HUGO_BUILD_TAGS=extended,withdeploy", "--provenance", "mode=max", "--sbom", "true", "--tag", "hugo-benchmark:local", "upstream"]

def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)

def main() -> int:
    try:
        command = tomllib.loads((ROOT / ".boringcache.toml").read_text())["adapters"]["docker"]["command"]
        require(command == EXPECTED, "Docker plan changed")
        upstream = (ROOT / "upstream/.github/workflows/image.yml").read_text()
        for fragment in ("context: .", "provenance: mode=max", "sbom: true", "platforms: linux/amd64,linux/arm64", "build-args: HUGO_BUILD_TAGS=extended,withdeploy", "push: ${{ github.event_name != 'pull_request' }}"):
            require(fragment in upstream, f"upstream image job changed: {fragment}")
        action = (ROOT / ".github/actions/hugo-docker-benchmark/action.yml").read_text()
        require(action.count("platforms: linux/amd64,linux/arm64") == 3, "provider platforms drifted")
        require(action.count("HUGO_BUILD_TAGS=extended,withdeploy") == 3, "provider tags drifted")
        require(action.count("sbom: true") == 3, "provider SBOM output drifted")
    except (KeyError, OSError, RuntimeError, tomllib.TOMLDecodeError) as error:
        print(f"Hugo recipe mismatch: {error}", file=sys.stderr)
        return 1
    print("Verified Hugo multi-platform image plan.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
