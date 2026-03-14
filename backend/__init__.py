import sys
from pathlib import Path

# Ensure project root is on sys.path even if commands are run from the backend/ directory.
_ROOT = Path(__file__).resolve().parent
_PROJECT_ROOT = _ROOT.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
