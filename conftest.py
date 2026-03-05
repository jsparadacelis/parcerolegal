import sys
from pathlib import Path

# Make the project root importable so `from data.scripts.X import Y` works
sys.path.insert(0, str(Path(__file__).parent))
