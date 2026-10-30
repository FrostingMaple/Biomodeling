"""Run the bundled Boolean example without API keys or network requests."""
import json
from pathlib import Path
import subprocess
import sys
import uuid

root = Path(__file__).resolve().parent
store = root / "runs" / ("boolean-" + uuid.uuid4().hex[:12])

def cli(*args):
    result = subprocess.run([sys.executable, "-m", "biomodel_agent", *map(str, args)],
                            cwd=root, text=True, capture_output=True)
    if result.returncode:
        sys.stderr.write(result.stderr or result.stdout)
        raise SystemExit(result.returncode)
    return json.loads(result.stdout)

if __name__ == "__main__":
    model = cli("typed-import", "--store", store, root / "examples/model-types/boolean.json")
    result = cli("typed-run", "--store", store, model["ref"], "--config",
                 root / "examples/model-types/boolean-settings.json")
    if not result["completion_eligible"]:
        raise SystemExit("Computation did not pass its numerical checks")
    (store / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(store), **result}, ensure_ascii=False, indent=2))
