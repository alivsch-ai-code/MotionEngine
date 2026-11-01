"""REST/JSON API of the platform: python run_api.py --port 8765 [--token SECRET]"""

import sys

from vdsim.api.server import main

if __name__ == "__main__":
    sys.exit(main())
