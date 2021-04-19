#!/usr/bin/env python

import os
import sys

if __package__ == "":
    path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, path)

from jsonschema2popo.jsonschema2popo import main as _main  # noqa

if __name__ == "__main__":
    # Reset argv[0] so that argparse will see this as the program name
    sys.argv[0] = "jsonschema2popo2"
    sys.exit(_main())
