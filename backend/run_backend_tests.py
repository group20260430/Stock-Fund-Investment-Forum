from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


TEST_SCRIPTS = [
    "test_sensitive_filter.py",
    "test_content_api.py",
    "test_interactions_api.py",
    "test_admin_api.py",
    "test_discovery_api.py",
    "test_community_api.py",
    "test_social_api.py",
    "test_e2e.py",
]


def _resolve_backend_dir() -> Path:
    current = Path(__file__).resolve()
    if current.parent.name == "backend":
        return current.parent
    return current.parent / "backend"


def _copy_backend_tree(source_backend_dir: Path, destination_root: Path) -> Path:
    destination_backend_dir = destination_root / "backend"
    shutil.copytree(
        source_backend_dir,
        destination_backend_dir,
        ignore=shutil.ignore_patterns("__pycache__", "*.db", ".venv*", ".pytest_cache"),
    )
    return destination_backend_dir


def _python_executable(backend_dir: Path) -> str:
    venv_python = backend_dir / ".venv313" / "Scripts" / "python.exe"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def _run_script(backend_dir: Path, script_name: str) -> int:
    script_path = backend_dir / script_name
    if not script_path.exists():
        print(f"{script_name}: FAIL (missing)")
        return 1

    with tempfile.TemporaryDirectory(prefix="backend-test-") as temp_root:
        temp_backend_dir = _copy_backend_tree(backend_dir, Path(temp_root))
        completed = subprocess.run(
            [_python_executable(backend_dir), str(Path(script_name))],
            cwd=str(temp_backend_dir),
            check=False,
        )
    if completed.returncode == 0:
        print(f"{script_name}: PASS")
        return 0
    print(f"{script_name}: FAIL (exit code {completed.returncode})")
    return 1


def main() -> int:
    backend_dir = _resolve_backend_dir()

    results: list[tuple[str, int]] = []
    for script_name in TEST_SCRIPTS:
        code = _run_script(backend_dir, script_name)
        results.append((script_name, code))

    passed = sum(1 for _, code in results if code == 0)
    failed = len(results) - passed

    print()
    print("BACKEND TEST SUMMARY")
    for script_name, code in results:
        print(f"* {script_name}: {'PASS' if code == 0 else 'FAIL'}")
    print()
    print(f"RESULTS: {passed} passed, {failed} failed")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
