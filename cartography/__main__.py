import sys
import pathlib

directory = pathlib.Path(__file__).parent.absolute()
sys.path.append(str(directory.parent))

import cartography.cli


if __name__ == '__main__':
    sys.exit(cartography.cli.main())
