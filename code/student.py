from util import *
import moss_interface
import git_interface

class Student(object):
  def __init__(self, student, course_dir, args):
    self.student = student
    self.course_dir = course_dir
    self.student_dir = os.path.join(course_dir, student)
    self.data_dir = args.data
    self.repo_dir = os.path.join(args.temp,
            '%s_%s' % (TEMP_REPO_DIR, student))
    coursename = os.path.basename(os.path.normpath(self.course_dir))
    self.out_student_dir = os.path.join(args.out, coursename,
                              self.student)
    self.top_match_path = os.path.join(self.out_student_dir, TOP_MATCHES)
    self.extension = args.extension
    self.matches = {}

  def get_name(self):
    return self.student

  """
  Returns a list of directories, where each
  directory corresponds to a student snapshot.
  """
  def setup_repository(self):
    counter = course_counts[self.course_dir]
    student_i = counter.get()
    num_students = counter.get_total()
    print "Student {}/{} {} setting up snapshot repository ...".format(
      student_i, num_students, self.student)
    if os.path.exists(self.repo_dir):
      self.snapshots = [os.path.join(self.repo_dir, snapshot) \
          for snapshot in os.listdir(self.repo_dir)]
      return
    git_interface.git_master(self.student_dir) # prepare
  
    # snapshot "hash timestamp"
    all_snapshots = git_interface.git_log(
                          git_dir=self.student_dir, format_str="%h %ct"
                          ).split('\n')
    self.snapshots = [0]*len(all_snapshots)
    for j, snapshot in enumerate(all_snapshots):
      snapshot_hash, snapshot_posix = snapshot.split(' ')
      human_time = posix_to_datetime(int(snapshot_posix))
      sys.stdout.write('{}/{} {} snapshot {} ({})\r'.format(
        j+1, len(all_snapshots), self.student_dir, snapshot_hash, human_time))
      sys.stdout.flush()
      snapshot_dir = git_interface.git_checkout(snapshot,
          orig_dir=self.student_dir, target_dir=self.repo_dir,
          prefix=self.student)
      self.setup_snapshot(snapshot_dir)
      self.snapshots[j] = snapshot_dir
    sys.stdout.write('\n')
    sys.stdout.flush()

    git_interface.git_master(self.student_dir) # reset

  """
  Separate directories for each java file.
  """
  def setup_snapshot(self, snapshot_dir):
    code_files = [fname for fname in os.listdir(snapshot_dir) \
        if fname.endswith(self.extension)]
    code_dirs = []
    for j, code_fname in enumerate(code_files):
      # remove all underscores
      code_newname = ''.join(code_fname.split('.')[0].split('_'))
      code_dir = os.path.join(snapshot_dir,
                '%s_%s' % (self.student,code_newname))
      if os.path.exists(code_dir):
        shutil.rmtree(code_dir)
      os.mkdir(code_dir)
      src = os.path.join(snapshot_dir, code_fname)
      dst = os.path.join(code_dir, code_fname)
      shutil.move(src, dst)
      code_dirs.append(code_dir)
    return code_dirs

  """
  Saves match to a dictionary.
  Also saves match to an html output to look at later.
  """
  def record_match(self, result):
    self.matches[result.get_snapshot()] = result
    result.write_csv(self.out_student_dir)
    result.write_html(self.out_student_dir)

  def load_match(self, snapshot_dir):
    snapshot = os.path.basename(os.path.normpath(snapshot_dir))
    return Result.load_csv(self.out_student_dir, snapshot)

  def get_matches(self):
    return [self.matches[snapshot] \
        for snapshot in sorted(self.matches.keys())]

  def is_match_computed(self, snapshot_dir):
    snapshot = os.path.basename(os.path.normpath(snapshot_dir))
    return snapshot in self.matches

  def save_top_match(self, top_match):
    write_csv(self.top_match_path, [top_match.get_tuple()])

  def get_top_match(self):
    if not os.path.exists(self.top_match_path):
      return None
    with open(self.top_match_path, 'r') as f:
      line = f.readline()
      return Result.parse_line(line)

  def cleanup(self):
    if os.path.exists(self.repo_dir):
      sys.stdout.write("{}: Removing expanded student repo ({})...\n".format(
        self.student, self.repo_dir))
      shutil.rmtree(self.repo_dir)

