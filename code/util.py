import os, sys, subprocess
import shutil
import re
import itertools
import pytz

import datetime, time
from multiprocessing import Pool as ThreadPool
from multiprocessing import Lock, Value
########################## Constants ######################
TEMP_REPO_DIR = 'repo'
TOP_MATCHES = 'top_matches.csv'
NUM_THREADS = 8 # if multiprocessing is turned on
pst = pytz.timezone('US/Pacific')
utc = pytz.utc

def call_cmd(cmd):
  return subprocess.Popen([cmd],stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()

def seconds_to_time(seconds):
  dec = ("%.4f" % (seconds % 1)).lstrip('0')
  m, s = divmod(seconds, 60)
  h, m = divmod(m, 60)
  return "%d:%02d:%02d%s" % (h, m, s, dec)

def posix_to_datetime(posix_t, format_str=None):
  if not format_str:
    format_str = '%m/%d %H:%M'
  return utc.localize(datetime.datetime.fromtimestamp(posix_t)).astimezone(pst).strftime(format_str)

course_counts = {}
def set_global_course_counts(course_dirs):
  course_counts.update(dict([(course_dir,
                        LockedCounter(len(os.listdir(course_dir)))) \
                        for course_dir in course_dirs]))
class LockedCounter(object):
  def __init__(self, total):
    self.lock = Lock()
    self.count = Value('i', 0)
    self.total = total
  
  def incr_and_get(self):
    with self.lock:
      self.count.value += 1
      return self.count.value

  def get(self):
    with self.lock:
      return self.count.value

  def get_total(self):
    return self.total

def write_csv(fpath, tuple_list):
  with open(fpath, 'w') as f:
    f.write('\n'.join([','.join(map(str, item)) for item in tuple_list]))
  print "--- Wrote csv to %s" % fpath


class Result(object):
  @staticmethod
  def parse_line(line):
    tup = line.strip().split(',')
    student, other, snapshot, score = tup
    return Result(student, snapshot, float(score), other)

  @staticmethod
  def load_csv(out_dir, snapshot):
    fdest = os.path.join(out_dir, "{}.csv".format(snapshot))
    if not os.path.exists(fdest):
      return None
    with open(fdest, 'r') as f:
      student, other, snapshot, score = Result.parse_line(f.readline()).get_tuple()
      return Result(student, snapshot, score, other)

  def __init__(self, student, snapshot, score=0, other=None):
    self.student = student
    self.snapshot = snapshot
    self.score = score
    self.other = ''
    if other:
      self.other = other

  def get_student(self):
    return self.student

  def get_snapshot(self):
    return self.snapshot
  
  def get_other(self):
    return self.other

  def get_score(self):
    return self.score

  def get_tuple(self):
    return (self.get_student(), self.get_other(),
        self.get_snapshot(), self.get_score())

  def write_csv(self, out_dir):
    fdest = os.path.join(out_dir, "{}.csv".format(self.get_snapshot()))
    if os.path.exists(fdest):
      return fdest
    if not os.path.exists(out_dir):
      os.makedirs(out_dir)
    write_csv(fdest, [self.get_tuple()])
    return fdest

  def write_html(self, out_dir):
    pass
