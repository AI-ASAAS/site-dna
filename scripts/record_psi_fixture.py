"""Record live PageSpeed Insights responses for Phase 6 fixtures.

This is a manual, live-only helper. Run it once with network access and an
optional PSI API key, then commit the sanitized JSON files:

    python scripts/record_psi_fixture.py --url https://example.com --out tests/fixtures/psi

The script never writes the API key to disk or logs. Responses are stored as
`{strategy}_live.json`; existing fixtures are not overwritten unless `--force`
is passed.
"""

import argparse
import asyncio
import json
import os
from pathlib import Path

import httpx

PSI_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


async def record(url: str, out_dir: Path, *, api_key: str | None, force: bool) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    params = {"url": url, "category": "performance"}
    if api_key:
        params["key"] = api_key

    async with httpx.AsyncClient(timeout=httpx.Timeout(90.0)) as client:
        for strategy in ("mobile", "desktop"):
            target = out_dir / f"{strategy}_live.json"
            if target.exists() and not force:
                print(f"skip {target} (exists; use --force to overwrite)")
                continue
            response = await client.get(PSI_ENDPOINT, params={**params, "strategy": strategy})
            target.write_text(
                json.dumps(response.json(), indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            print(f"wrote {target} ({response.status_code})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="https://example.com")
    parser.add_argument("--out", type=Path, default=Path("tests/fixtures/psi"))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    api_key = os.environ.get("PSI_API_KEY") or None
    asyncio.run(record(args.url, args.out, api_key=api_key, force=args.force))


if __name__ == "__main__":
    main()
