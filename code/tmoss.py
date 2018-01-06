from util import *
from moss_interface import compute_similarity, cleanup_similarity_workspace
import git_interface
from student import Student

"""
Main TMOSS file.

Owner:
Lisa Yan <yanlisa@stanford.edu>
"""
#################################### Setup ####################################
"""
Returns a set of top-level directories for comparing against on a backend.
"""
def get_compare_set(course_dir, args):
  online_dir = args.online
  final_submissions_dir = setup_final_submissions(course_dir, args)
  return final_submissions_dir, online_dir

"""
One file per directory, otherwise moss similarity scores will be off.

student_dir/
  file_one.java
  file_two_point_five.java
  file_notjava.c
  README.txt
----> turns into --->
studentdir_fileone/
  file_one.java
studentdir_filetwopointfive/
  file_two_point_five.java
"""
def setup_final_submissions(course_dir, args):
  course_dir = course_dir.strip('/')
  course_name = course_dir.split('/')[-1]
  data_dir = '/'.join(course_dir.split('/')[:-1])
  final_submissions_dir = os.path.join(data_dir,
      '%s_%s' % (args.final_submissions, course_name))
  if os.path.exists(final_submissions_dir):
    print "Already exists: {}".format(final_submissions_dir)
    return final_submissions_dir
  os.mkdir(final_submissions_dir)
  print "Preparing final submission directories. " + \
      "This only needs to be done once."

  git_interface.reset_all_to_master(course_dir)
  for i, student in enumerate(os.listdir(course_dir)):
    student_dir = os.path.join(course_dir, student)
    if not os.path.isdir(student_dir): continue
    student_newname = ''.join(student.split('_')) # remove underscores

    code_files = [fname for fname in os.listdir(student_dir) \
        if fname.endswith(args.extension)]
    for j, code_fname in enumerate(code_files):
      # remove all underscores
      code_newname = ''.join(code_fname.split('.')[0].split('_'))
      code_dirname = '%s_%s' % (student_newname, code_newname)
      code_dir = os.path.join(final_submissions_dir, code_dirname)
      sys.stdout.write('{}/{}: {}/{} {}\r'.format(
        i+1, len(course_dir), j+1, len(code_files),
        os.path.join(code_dirname, code_fname)))
      sys.stdout.flush()
      os.mkdir(code_dir)
      src = os.path.join(student_dir, code_fname)
      dst = os.path.join(code_dir, code_fname)
      shutil.move(src, dst)
  sys.stdout.write('\n')
  sys.stdout.flush()
  return final_submissions_dir

############################### Helper functions #############################
def argmax_result(results):
  return max(results, key=lambda result: result.get_score())

def load_top_matches(course_dir, out_dir, fname=None):
  if not fname:
    fname = TOP_MATCHES
  coursename = os.path.basename(os.path.normpath(course_dir))
  out_course_dir = os.path.join(out_dir, coursename)
  top_matches_path = os.path.join(out_course_dir, fname)
  if not os.path.exists(top_matches_path):
    return []
  print "Found top matches at {}".format(top_matches_path)
  with open(top_matches_path, 'r') as f:
    return [Result.parse_line(line) for line in f.readlines()]

def save_top_matches(top_matches, course_dir, args):
  # first filter out for null matches.
  top_matches = filter(lambda x: x, top_matches)

  coursename = os.path.basename(os.path.normpath(course_dir))
  out_course_dir = os.path.join(args.out, coursename)
  top_matches_path = os.path.join(out_course_dir, TOP_MATCHES)
  top_match_tuples = [top_match.get_tuple() for top_match in top_matches]
  write_csv(top_matches_path, top_match_tuples)

################################### Cleanup ###################################
def cleanup_student(student, args):
  student = os.path.basename(os.path.normpath(student_dir))

  repo_dir = os.path.join(args.data,
      '%s_%s' % (TEMP_REPO_DIR, student))
  sys.stdout.write("{}: Removing expanded student submissions ({})...".format(
    student, TEMP_REPO_DIR))
  pass

def cleanup(args):
  if os.path.exists(args.temp):
    print "Removing temporary directory..."
    shutil.rmtree(args.temp)

################################# Algorithm 1 #################################
"""
Main TMOSS algorithm.
Input:
  course_dir: Path for course directory.
  online_dir: Path for online directory.

Output:
  nothing. Saves top matches to a file.
"""
def tmoss(course_dir, args):
  start_time = time.time()
  top_matches = load_top_matches(course_dir, args.out)
  if top_matches: # already processed
    print "Already processed {}".format(course_dir)
    return top_matches
  
  top_matches = get_top_matches(course_dir, args)
  save_top_matches(top_matches, course_dir, args)
  cleanup(args)   # course cleanup
  end_time = time.time()
  print "Runtime for {}: took {}".format(course_dir,
        seconds_to_time(end_time - start_time))


def get_top_matches(course_dir, args):
  compare_set = get_compare_set(course_dir, args)
  if args.multithread:
    pool = ThreadPool(NUM_THREADS)
    zipped_args = [(student_name, course_dir, compare_set, args) \
        for student_name in sorted(os.listdir(course_dir))][14:15]
    top_matches = pool.map(get_top_match, zipped_args)
    top_matches = filter(lambda x: x, top_matches)
  else:
    top_matches = []
    for student_name in sorted(os.listdir(course_dir))[:3]:
      zipped_arg = (student_name, course_dir, compare_set, args)
      top_match = get_top_match(zipped_arg)
      if not top_match:
        print "{} was not a valid git repository.".format(student_name)
        continue
      top_matches.append(top_match)
  return top_matches

def get_top_match(zipped_arg):
  student_name, course_dir, compare_set, args = zipped_arg
  counter = course_counts[course_dir]
  student = Student(student_name, course_dir, args)
  student_i = counter.incr_and_get()
  num_students = counter.get_total()

  top_match = student.get_top_match()
  if top_match:
    print "Student {}/{} {} already processed".format(
      student_i, num_students, student_name)
    return top_match

  ### setup
  student.setup_repository()

  ### for each snapshot, compute similarity
  for j, snapshot_dir in enumerate(sorted(student.snapshots)):
    print "Student {}/{} {} snapshot {}/{} ...".format(
      student_i, num_students, student_name,
      j+1, len(student.snapshots))
    result = student.load_match(snapshot_dir)
    if not result:
      results = compute_similarity(snapshot_dir, compare_set, student, args)
      result = argmax_result(results)
    student.record_match(result)
    cleanup_similarity_workspace(snapshot_dir, args)

  if not student.get_matches():
    return None
  top_match = argmax_result(student.get_matches())
  student.save_top_match(top_match)
  ### cleanup
  student.cleanup()

  return top_match

