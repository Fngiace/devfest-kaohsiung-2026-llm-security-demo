from pathlib import Path
import subprocess
import sys
from naive_grader import WARNING


print(WARNING, flush=True)
here = Path(__file__).parent
valid = True
for name in ("no_assertions", "graded_full_output", "healthy"):
    outcomes = []
    for grader in ("naive", "strict"):
        result = subprocess.run([sys.executable, str(here / f"{grader}_grader.py"), str(here / "fixtures" / f"{name}.json")],
                                capture_output=True, text=True)
        outcomes.append(result)
    print(f"\n{name}\nnaive | strict")
    print(outcomes[0].stdout.rstrip().split("\n", 1)[-1] + " | " + outcomes[1].stdout.rstrip().split("\n", 1)[-1])
    print(f"exit codes: naive={outcomes[0].returncode}; strict={outcomes[1].returncode}")
    valid &= outcomes[0].returncode == 0 and outcomes[1].returncode == (0 if name == "healthy" else 1)
raise SystemExit(0 if valid else 1)
