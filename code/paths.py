# filepaths hardcoded. 

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent   # code/paths.py -> code/ -> project root
RAW = ROOT / 'data' / 'raw'
DERIVED = ROOT / 'data' / 'derived'
FIGURES = ROOT / 'figures'