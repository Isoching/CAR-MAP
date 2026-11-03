"""Run the frozen V7 reproduction scripts without changing archived results."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

from prepare_data import ROOT, prepare


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("quick", "full"), default="full",
                        help="quick: archive, 40 matrix examples and derived accounts; full: also regenerate 1700 controls and their matrices")
    parser.add_argument("--output", type=Path, default=ROOT / "reproduced")
    args = parser.parse_args()
    output = args.output.resolve()
    if output == ROOT / "paper" or (ROOT / "paper").resolve() in output.parents:
        parser.error("Write new results outside the frozen paper/ tree")
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    preparation = prepare()
    code = ROOT / "paper/code"
    steps = [
        ("validate_archive.py", ["--report", str(output / "archive_validation.json")]),
        ("replay_matrix_examples.py", ["--report", str(output / "matrix_replay.json")]),
        ("check_derived_accounts.py", ["--report", str(output / "derived_accounts.json")]),
    ]
    if args.mode == "full":
        steps += [
            ("run_control_calculations.py", ["--output", str(output / "controls")]),
            ("compare_controls.py", ["--candidate", str(output / "controls"),
                                     "--report", str(output / "control_comparison.json")]),
            ("export_control_matrices.py", ["--output", str(output / "CONTROL_LP_MATRICES.json")]),
        ]
    completed = []
    for name, arguments in steps:
        command = [sys.executable, str(code / name), *arguments]
        print(f"\nRunning {name}", flush=True)
        result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        (output / f"{Path(name).stem}.log").write_text(result.stdout, encoding="utf-8")
        print(result.stdout, end="", flush=True)
        if result.returncode:
            raise SystemExit(f"{name} failed (exit {result.returncode}); see {output}")
        completed.append(name)
    packages = {name: importlib.metadata.version(name)
                for name in ("numpy", "scipy", "CoolProp", "openpyxl")}
    report = {"status": "PASS", "mode": args.mode, "completed_utc": datetime.now(timezone.utc).isoformat(),
              "python": platform.python_version(), "platform": platform.platform(),
              "packages": packages, "preparation": preparation, "completed_steps": completed,
              "elapsed_seconds": round(time.monotonic() - started, 2),
              "scope": "Frozen-payload integrity, 40 matrix examples and derived accounts. Full mode additionally regenerates and compares all 1700 V7 control solutions and reconstructs their matrices; this is not a regeneration of every original figure grid or figure artwork."}
    (output / "RUN_SUMMARY.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"\nPASS: {args.mode} reproduction. Reports: {output}")


if __name__ == "__main__":
    main()
