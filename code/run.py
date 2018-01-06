from util import set_global_course_counts
from tmoss import tmoss
from argparse import ArgumentParser
import os

parser = ArgumentParser(description="TMOSS Algorithm")
parser.add_argument('--data', '-d',
        type=str,
        help="Directory of student repositories sorted by course",
        default="data")

# backend software similarity detector is assumed to be at bin.

parser.add_argument('--out', '-o',
        type=str,
        help="Destination for outputting matches.",
        default="out")

parser.add_argument('--final-submissions', '-final',
        type=str,
        help="Final submissions. Should be located under data directory. Can be created with this script.",
        default="final_submissions")

parser.add_argument('--online', '-x',
        type=str,
        help="Online submissions. Should not be located under data directory",
        default="online")

parser.add_argument('--starter', '-s',
        type=str,
        help="Starter code. Should be located under data directory",
        default="starter")

parser.add_argument('--extension', '-ext',
        type=str,
        help="Student code extension type.",
        default="java")

parser.add_argument('--temp', '-temp',
        type=str,
        help="Temp workspace directory.",
        default="temp")

parser.add_argument('--multithread', '-m',
        help="Turn on multiprocessing",
        action='store_true')
args = parser.parse_args()

def get_course_dirs(args):
  course_dirs = []
  for course in sorted(os.listdir(args.data)):
    course_dir = os.path.join(args.data, course)
    if course == args.online: continue
    if args.final_submissions in course: continue
    if not os.path.isdir(course_dir): continue
    course_dirs.append(course_dir)
  return course_dirs

if __name__ == "__main__":
  course_dirs = get_course_dirs(args)
  set_global_course_counts(course_dirs)
  for course_dir in course_dirs:
    tmoss(course_dir, args)
