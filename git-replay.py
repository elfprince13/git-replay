#!/usr/bin/env python3

import argparse
import os
import re
from subprocess import Popen, PIPE

def git(*args,stdin=None,auto_rstrip=True,env=None):
	command = ["git"]+list(args)
	gitp = Popen(command,stdin=stdin,stderr=PIPE,stdout=PIPE,env=env)
	(outs, errs) = gitp.communicate()
	status = gitp.returncode
	if status == 0:
		outs = outs.decode()
		return outs.rstrip() if auto_rstrip else outs
	else:
		errs = errs.decode()
		raise RuntimeError("Process from command-line %s exited with status %d and error log:%s\n" % (repr(command), status, errs))
	
def git_formatted_log(fmt, commit): return git("log","-1","--pretty=format:%s" % fmt,commit)

def git_author_name(commit): return git_formatted_log("%an", commit)
def git_author_email(commit): return git_formatted_log("%ae", commit)
def git_author_date(commit): return git_formatted_log("%ad", commit)
def git_committer_name(commit): return git_formatted_log("%cn", commit)
def git_committer_email(commit): return git_formatted_log("%ce", commit)
def git_committer_date(commit): return git_formatted_log("%cd", commit)

def git_head(): return git("rev-parse","HEAD")


commit_seq = re.compile(r"^(commit(?: [0-9a-f]{40})+)$",flags=re.MULTILINE)
def git_find_replay_list(relative, upto):
	log = git("log","--parents","--pretty=fuller","--no-decorate","%s..%s" % (relative, upto))
	commits = commit_seq.findall(log)
	return [commit.split(" ")[1:] for commit in reversed(commits)]

def git_cherry_pick(commit,mainline=None,cross_ref=True,process_committer_meta=None):
	args = (("-m",mainline) if mainline else ()) + (("-x",) if cross_ref else ()) + (commit,)
	if process_committer_meta:
		env = dict(os.environ)
		committer_meta = {"name" : git_committer_name(commit),
						  "email" : git_committer_email(commit),
						  "date" : git_committer_date(commit)}
		env["GIT_COMMITTER_NAME"] = process_committer_meta["name"](committer_meta)
		env["GIT_COMMITTER_EMAIL"] = process_committer_meta["email"](committer_meta)
		env["GIT_COMMITTER_DATE"] = process_committer_meta["date"](committer_meta)
	else:
		env = None
	return git("cherry-pick",*args,env=env)
	

def main(badname, bademail, goodname, goodemail, relative, upto, into):
	commits = git_find_replay_list(relative, upto)
	print(git("checkout",commits[0][1]))
	print(git("checkout","-b",into))
	print(git("submodule","update"))
	
	process_committer_meta = {"name" : (lambda meta: goodname if meta["name"] == badname and meta["email"] == bademail else meta["name"]),
							  "email": (lambda meta: goodemail if meta["name"] == badname and meta["email"] == bademail else meta["email"]),
							  "date" : (lambda meta: meta["date"])}
	
	for commit_info in commits:
		commit = commit_info[0]
		parents = commit_info[1:]
		print("Processing %s" % commit)
		try:
			print(git_cherry_pick(commit,mainline="1" if len(parents) > 1 else None,process_committer_meta=process_committer_meta))
		except RuntimeError as err:
			print(err.args)
			if len(err.args) == 1 and ("cherry-pick is now empty," in err.args[0]):
				print(git("cherry-pick","--skip"))
			else:
				raise err
		finally:
			print(git("submodule","update"))
		
		# Now amend the author.
		# This time we just preserve the committer meta,
		# because we've already processed it if need-be while cherry-picking
		head = git_head()
		print("Git HEAD: %s" % head)
		author_name = git_author_name(head)
		author_email = git_author_email(head)
		author_date = git_author_date(head)
		
		author_string = "%s <%s>" % ((goodname, goodemail) if author_name == badname and author_email == bademail else (author_name, author_email))
		print("New author info: %s" % author_string)
		
		env = dict(os.environ)
		env["GIT_COMMITTER_NAME"] = git_committer_name(head)
		env["GIT_COMMITTER_EMAIL"] = git_committer_email(head)
		env["GIT_COMMITTER_DATE"] = git_committer_date(head)
		
		print(git("commit","--amend","--author='%s'" % author_string,"--date='%s'" % author_date,"--no-edit",env=env))
		
	print("Done")
	print(git("checkout",upto))

if __name__ == '__main__':
	import sys
	main(*sys.argv[1:])