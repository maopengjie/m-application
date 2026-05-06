#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_PYTHON = ROOT / "apps" / "backend" / "venv" / "bin" / "python"


def run_step(name: str, command: list[str]) -> None:
    print(f"\n==> {name}")
    subprocess.run(command, cwd=ROOT, check=True)


def python_command() -> str:
    if BACKEND_PYTHON.exists():
        return str(BACKEND_PYTHON)
    return sys.executable


def main() -> int:
    python = python_command()
    run_step(
        "data-center env template check",
        [sys.executable, "scripts/check_data_center_config.py", "--env-file", ".env.example"],
    )
    run_step(
        "backend closure unit tests",
        [python, "-m", "unittest", "apps.backend.tests.test_data_center_closure", "-v"],
    )
    run_step(
        "python syntax check",
        [
            sys.executable,
            "-m",
            "py_compile",
            "apps/backend/api/data_cleaning.py",
            "apps/backend/api/sku_repository.py",
            "apps/backend/services/anomaly_recovery.py",
            "apps/backend/services/task_runs.py",
            "apps/worker/celery_app.py",
            "apps/worker/tasks/scraping.py",
            "scripts/check_data_center_config.py",
            "scripts/verify_data_center_e2e.py",
        ],
    )
    run_step(
        "web element typecheck",
        ["pnpm", "--dir", "apps/web-ele", "typecheck"],
    )
    print("\nok data-center CI checks")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from exc
