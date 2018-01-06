from util import *
import os
import pymoss


"""
Assumes that the user has access to a moss binary.

You can learn more about getting moss here:
  https://theory.stanford.edu/~aiken/moss/

Part of this code is thanks to Michael Chang <mchang91@stanford.edu>
"""
#### Constants
THRESHOLD = 1000000
# Patterns of files to check per language
MATCH_FILES = {
    "ascii": {"*"},
    "c": {"*.c", "*.h"},
    "cc": {"*.cc", "*.cpp", "*.h"},
    "java": {"*.java"}
}
STARTER, CURRENT, ARCHIVE, NTYPES = range(4)
TYPE_STR = ["STARTER", "CURRENT", "ARCHIVE"]

##### TMOSS interface function
def compute_similarity(snapshot_dir, archives, student, args):
  snapshot = os.path.basename(os.path.normpath(snapshot_dir))
  snapshot_dir = os.path.realpath(snapshot_dir)
  filelang = args.extension
  final_submissions_dir, online_dir = archives

  runner = make_moss_runner(filelang, snapshot_dir,
          final_submissions_dir, online_dir,
          args.starter)

  output_temp_dir = os.path.join(args.temp, 'moss_%s' % snapshot)
  if os.path.exists(output_temp_dir):
    shutil.rmtree(output_temp_dir)
  gen_moss_output(runner, snapshot, output_temp_dir)
  return make_results(student.get_name(), runner, snapshot, args)

def cleanup_similarity_workspace(snapshot_dir, args):
  snapshot = os.path.basename(os.path.normpath(snapshot_dir))
  output_temp_dir = os.path.join(args.temp, 'moss_%s' % snapshot)
  if os.path.exists(output_temp_dir):
    shutil.rmtree(output_temp_dir)

##### Helper functions
def make_results(student, runner, snapshot, args):
  # ignore all self ones
  results = [MossResult(pair, runner, snapshot, args) \
          for pair in runner.pairs if not pair.is_self]
  if not results:
    results = [Result(student, snapshot)] # empty result
  return results

def make_moss_runner(filelang, snapshot_dir,
    final_submissions_dir, online_dir, starter_dir):
  snapshot = os.path.basename(os.path.normpath(snapshot_dir))
  m = pymoss.Runner(filelang, THRESHOLD)
  if os.path.exists(starter_dir):
    m.add(starter_dir, pymoss.util.STARTER)
  m.add_all(snapshot_dir, prefix=snapshot)
  m.add_all(final_submissions_dir, pymoss.util.ARCHIVE)
  if os.path.exists(online_dir):
    m.add_all(online_dir, pymoss.util.ARCHIVE)
  return m

def gen_moss_output(moss_runner, snapshot, output_temp_dir):
  print "--- Running MOSS on", snapshot
  if os.path.exists(output_temp_dir):
    shutil.rmtree(output_temp_dir)
  moss_runner.run(output_temp_dir)
  print

##### TMOSS Result object
"""
Results will be saved for each quarter.
out/
  2012_1/
    top_matches.csv # student,token,timestamp,snapshot_num
    student/
      top_match_html
      student_matches.csv
"""
class MossResult(pymoss.Pair, Result):
  def __init__(self, pair, runner, snapshot, args):
    # copied from Pair in code/pymoss/util.py
    for k, v in pair.__dict__.iteritems():
      self.__dict__[k] = v

    self.student = self.submits[0].student()
    self.other = self.submits[1].student()
    self.runner = runner
    self.args = args
    self.snapshot = snapshot
    """
    Score:
      self.match:   matched token count
      self.common:  matched "common" tokens (including starter code)
      self.percent: (% snapshot, % similarity)
    """
    self.score = self.tokens.match
    
  def write_html(self, out_dir):
    if not os.path.exists(out_dir):
      os.makedirs(out_dir)
    fdest = os.path.join(out_dir, "{}.html".format(self.get_snapshot()))
    if os.path.exists(fdest):
      os.remove(fdest)
    h = pymoss.Html(self.runner, self.get_snapshot())
    h.gen_report(self, fdest)
    print "--- Writing MOSS HTML to", fdest
