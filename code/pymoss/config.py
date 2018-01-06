"""
pymoss.config -- Configuration variables

Michael <mchang@cs>, 2015
"""

import os

# Whether archived submissions have a submission number in their directory name
HAS_SUBMIT_NUM = True

# Patterns of files to check per language
MATCH_FILES = {
    "ascii": {"*"},
    "c": {"*.c", "*.h"},
    "cc": {"*.cc", "*.cpp", "*.h"},
    "java": {"*.java"}
}

# Default number of pairs to report (can be changed as arg to run())
NPAIRS = 2

# Default number of occurrences before code is considered common (can be set in Moss constructor)
THRESHOLD = 100000000
THRESHOLD = 10

#--- Directories ---#

# Location to store report output (html)
# - Files accessible at https://web.stanford.edu/dept/cs_edu/moss/
#OUTDIR = "/afs/ir/dept/cs_edu/WWW/moss"
# - Use cwd at the time pymoss is imported (probably the dir the script is run from)
OUTDIR = os.getcwd()

# Location to store temporary files
# NOTE: Don't use a directory in /afs, or everything will run very slowly.
# - Use TMPDIR from environment (e.g. /tmp)
TMPDIR = None
# - Use tmp dir inside pymoss directory
#TMPDIR = os.path.realpath(os.path.join(os.path.dirname(__file__), "tmp"))

# Base URL to return for generated reports.
# (This doesn't have to actually work, e.g. if OUTDIR is not served by a web server.)
#URL = "https://web.stanford.edu/dept/cs_edu/moss/"
URL = "./"

# vim: et sw=4 ts=4

