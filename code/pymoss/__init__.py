"""
PyMOSS -- A Python library for MOSS

Michael <mchang@cs>, 2015

This package provides Python bindings to interact with the MOSS binary.
"""

import os, sys
sys.path.insert(1, os.path.realpath(os.path.join(os.path.dirname(__file__), "lib")))

__all__ = ["config", "html", "runner", "util"]
from . import config
from .html import Html
from .runner import Runner
from .util import *

# vim: et sw=4 ts=4

