from util import *
import os, sys, subprocess

def reset_all_to_master(code_dir):
  print code_dir
  tot_students = len(os.listdir(code_dir))
  for i, student in enumerate(os.listdir(code_dir)):
    sys.stdout.write("{}/{}: Reset to master ({})\r".format(
      i+1, tot_students, student))
    sys.stdout.flush()
    student_dir = os.path.join(code_dir, student)
    git_master(student_dir)
  sys.stdout.write('\n')

############### low-level git #######################

def git_diff(commit1, commit2, git_dir=None, git_name=None, lines=-1, format_str=None, extra_str=None):
  if not git_name:
    git_name = ".git"
  if git_dir:
    git_name = os.path.join(git_dir, git_name)

  lines_str = ''
  if lines != -1:
    lines_str = "-%d" % lines

  if not format_str:
    format_str = ''
  else:
    format_str = "--pretty=format:'%s'" % format_str

  if not extra_str:
    extra_str = ''

  cmd = "git --git-dir %s diff %s %s %s %s" % \
    (git_name, lines_str, format_str, commit1, commit2)

  ret_str, log_err = call_cmd(cmd)
  if 'fatal' in log_err: return ''
  return ret_str

def git_log(git_dir=None, git_name=None, lines=-1, format_str=None, extra_str=None):
  if not git_name:
    git_name = ".git"
  if git_dir:
    git_name = os.path.join(git_dir, git_name)

  lines_str = ''
  if lines != -1:
    lines_str = "-%d" % lines

  if not format_str:
    format_str = ''
  else:
    format_str = "--pretty=format:'%s'" % format_str

  if not extra_str:
    extra_str = ''

  cmd = "git --git-dir %s log %s %s %s" % \
    (git_name, lines_str, format_str, extra_str)

  ret_str, log_err = call_cmd(cmd)
  if 'fatal' in log_err: return ''
  return ret_str

"""
Reverts a student dir to the git hash listed.

If target_dir given, copy the snapshot to
  target_dir/<commit timestamp>_<commit hash>

Note: does *not* revert student directory to master.
Expected commit format: %h %ct <commit short hash> <unix timestamp>
"""
def git_checkout(commit, orig_dir, git_name=None,target_dir=None, prefix=None):
  if not git_name:
    git_name = ".git"

  commit_hash, posix_time = commit.split(' ')

  if target_dir: # check if already expanded
    target_commit_dir = os.path.join(target_dir,
                     "%s_%s_%s" % (prefix, posix_time, commit_hash))
    #print "copying to target", target_commit_dir
    if os.path.exists(target_commit_dir):
      #print "\tSkipping. Already copied to", target_commit_dir
      return target_commit_dir
    else:
      #print "Expand to", target_commit_dir
      os.makedirs(target_commit_dir)

  git_dir = os.path.join(orig_dir, git_name)
  checkout_cmd = "git --git-dir=%s --work-tree=%s checkout %s" % \
    (git_dir, orig_dir, commit_hash)
  _, checkout_err = call_cmd(checkout_cmd)

  if target_dir:
    # ignore hidden files
    cp_cmd = "cp -r %s/* %s" % (orig_dir, target_commit_dir)
    call_cmd(cp_cmd)
  return target_commit_dir
    
"""
Gets latest snapshot (the last one that the student submitted).
"""
def git_master(orig_dir, git_name=None):
  if not git_name:
    git_name = ".git"
  git_dir = os.path.join(orig_dir, git_name)
  
  # git checkout -f: discard local changes
  master_cmd = "git --git-dir=%s --work-tree=%s checkout -f master" \
    % (git_dir, orig_dir) 
  out, master_cmd_err = call_cmd(master_cmd)
  if 'error' in master_cmd_err:
    print "master: ignoring %s, corrupt git" % (orig_dir.split('/')[-1])
