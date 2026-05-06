#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


REQUIRED_KEYS = (
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
    "REDIS_URL",
    "ENABLE_DEMO_SEED",
    "ENABLE_PERIODIC_SCRAPE",
    "PERIODIC_SCRAPE_INTERVAL_MINUTES",
    "PERIODIC_SCRAPE_LIMIT",
    "MAINTENANCE_INTERVAL_MINUTES",
)


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def parse_int(values: dict[str, str], key: str, errors: list[str]) -> int | None:
    try:
        return int(values.get(key, ""))
    except ValueError:
        errors.append(f"{key} must be an integer")
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Check data-center deployment environment.")
    parser.add_argument("--env-file", default=".env", help="Path to the env file to check")
    parser.add_argument("--production", action="store_true", help="Enable stricter production checks")
    args = parser.parse_args()

    env_path = Path(args.env_file)
    if not env_path.exists():
        raise SystemExit(f"FAIL env file not found: {env_path}")

    values = parse_env(env_path)
    errors: list[str] = []
    warnings: list[str] = []

    for key in REQUIRED_KEYS:
        if key not in values:
            errors.append(f"missing {key}")

    interval = parse_int(values, "PERIODIC_SCRAPE_INTERVAL_MINUTES", errors)
    scrape_limit = parse_int(values, "PERIODIC_SCRAPE_LIMIT", errors)
    maintenance_interval = parse_int(values, "MAINTENANCE_INTERVAL_MINUTES", errors)

    if interval is not None and interval < 5:
        errors.append("PERIODIC_SCRAPE_INTERVAL_MINUTES should be at least 5")
    if scrape_limit is not None and not 1 <= scrape_limit <= 200:
        errors.append("PERIODIC_SCRAPE_LIMIT must be between 1 and 200")
    if maintenance_interval is not None and maintenance_interval < 1:
        errors.append("MAINTENANCE_INTERVAL_MINUTES should be at least 1")

    if values.get("POSTGRES_PASSWORD") in {"", "postgres"}:
        message = "POSTGRES_PASSWORD is using the default value"
        if args.production:
            errors.append(message)
        else:
            warnings.append(message)

    if values.get("ENABLE_DEMO_SEED", "").lower() in {"1", "true", "yes"}:
        message = "ENABLE_DEMO_SEED is enabled"
        if args.production:
            errors.append(message)
        else:
            warnings.append(message)

    for warning in warnings:
        print(f"WARN {warning}")
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1

    print("ok data-center env config")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
