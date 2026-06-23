from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def _write_text(text: str) -> None:
    if not text:
        return
    encoded = text.encode(sys.stdout.encoding or "utf-8", errors="replace")
    sys.stdout.buffer.write(encoded)
    if not text.endswith("\n"):
        sys.stdout.buffer.write(b"\n")
    sys.stdout.flush()


def _print_section(title: str) -> None:
    print(f"=== {title} ===")


def _run_backend_checks() -> int:
    script_path = BACKEND_DIR / "run_backend_tests.py"
    if not script_path.exists():
        print(f"Missing backend runner: {script_path}")
        return 1

    completed = subprocess.run(
        [sys.executable, script_path.name],
        cwd=str(BACKEND_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    _write_text(completed.stdout)
    _write_text(completed.stderr)
    return completed.returncode


def _resolve_npm_command() -> str:
    if sys.platform.startswith("win"):
        return shutil.which("npm.cmd") or "npm.cmd"
    return shutil.which("npm") or "npm"


def _run_frontend_build() -> int:
    completed = subprocess.run(
        [_resolve_npm_command(), "run", "build"],
        cwd=str(FRONTEND_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    _write_text(completed.stdout)
    _write_text(completed.stderr)
    return completed.returncode


def main() -> int:
    _print_section("Backend tests")
    backend_code = _run_backend_checks()

    print()
    _print_section("Frontend build")
    frontend_code = _run_frontend_build()

    results = [
        ("Backend tests", backend_code == 0),
        ("Frontend build", frontend_code == 0),
    ]
    passed = sum(1 for _, ok in results if ok)
    failed = len(results) - passed

    print()
    _print_section("Project check summary")
    for name, ok in results:
        print(f"* {name}: {'PASS' if ok else 'FAIL'}")
    print()
    print(f"RESULTS: {passed} passed, {failed} failed")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
