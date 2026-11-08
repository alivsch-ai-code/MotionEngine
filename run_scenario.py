"""Command line: run scenarios, print KPIs, export results and reports (see vdsim/cli/scenario.py).

    python run_scenario.py --list
    python run_scenario.py iso_doppelspurwechsel_80 --plot
"""

import sys

from vdsim.cli.scenario import main

if __name__ == "__main__":
    sys.exit(main())
