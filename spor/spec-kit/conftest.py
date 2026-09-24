"""Put the track root on sys.path so tests can `import todo`.

pytest's default (prepend) import mode inserts the directory of each test
file's rootdir package, not this one, so without this the tests collected
from `tests/` would not see the `todo` package.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
