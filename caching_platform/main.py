#!/usr/bin/env python3
"""Main entry point for the OpenAI-Style Caching Infrastructure Platform."""

import sys
import os

# Add the package to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from caching_platform.cli.interface import main

if __name__ == "__main__":
    main()