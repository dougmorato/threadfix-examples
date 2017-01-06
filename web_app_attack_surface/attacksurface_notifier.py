#!/usr/bin/python

from git import Git
from git import Repo
from hypchat import HypChat
import json
from optparse import OptionParser
import os
from slacker import Slacker
import StringIO
import time

execfile('attack_surface_lib.py')

parser = OptionParser()
parser.add_option('--repolocation', dest='repolocation', help='Path to Git repository location')
parser.add_option('--branch', dest='branch', help='Branch in the Git repository')
parser.add_option('--hipchat_token', dest='hipchat_token', help='HipChat API token')
parser.add_option('--hipchat_room', dest='hipchat_room', help='HipChat room name')
parser.add_option('--slack_token', dest='slack_token', help='Slack API token')
parser.add_option('--slack_room', dest='slack_room', help='Slack room name')


(options, args) = parser.parse_args()

do_hipchat = False
do_slack = False
do_jira = False

# Set up Git stuff
repo_path = options.repolocation
branch = options.branch
if branch == None:
	branch = 'master'

if repo_path == None:
	print 'Must enter a Git repository path. Exiting.'
	exit(-1)

# Set up HipChat stuff
hipchat_access_token = options.hipchat_token
hipchat_room_name = options.hipchat_room
hc = None
hc_room = None

print hipchat_access_token

if hipchat_access_token != None:
	do_hipchat = True
	print 'Will be sending messages to HipChat room: ' + hipchat_room_name
	hc = HypChat(hipchat_access_token)
	hc_room = hc.get_room(hipchat_room_name)

# Set up Slack stuff
slack_access_token = options.slack_token
slack_room_name = options.slack_room
slack = None

if slack_access_token != None:
	do_slack = True
	print 'Will be sending message to Slack channel: ' + slack_room_name
	slack = Slacker(slack_access_token)

# Set up Git stuff

repo = Repo(repo_path)
git = Git(repo_path)
head = repo.heads[0]
commits = list(repo.iter_commits(branch))

starting_commit_hash = commits[0].hexsha

# Say howdy

hello_message = 'ThreadFix Attack Surface bot is now active and we are keeping an eye on branch ' + branch + ' starting with commit ' + starting_commit_hash
if do_hipchat:
	hc_room.message(hello_message)

if do_slack:
	slack.chat.post_message(slack_room_name, hello_message)

while 1:
	# Check current commit
	git.checkout(branch)
	repo.remotes.origin.pull()
	commits = list(repo.iter_commits(branch))
	latest_commit_hash = commits[0].hexsha
	if latest_commit_hash != starting_commit_hash:
		# Have a new commit. Let's see if there are changes
		print 'Have a new commit: ' + latest_commit_hash
		print 'Checking attack surface for changes'
		attack_surface_diff = compare_git_commits(repo_path, branch, starting_commit_hash, latest_commit_hash)
		if len(attack_surface_diff.added) > 0 or len(attack_surface_diff.deleted) > 0:
			# Attack surface has changed
			chat_message = 'The ThreadFix Attack Surface chat bot has identified that commit: ' + latest_commit_hash + '\n'
			chat_message += 'Added attack surface: ' + ', '.join(attack_surface_diff.added) + '\n'
			chat_message += 'Deleted attack surface: ' + ', '.join(attack_surface_diff.deleted)
			print chat_message

			if do_hipchat:
				hc_room.message(chat_message)

			if do_slack:
				slack.chat.post_message(slack_room_name, chat_message)
			
			print 'Updating latest commit to: ' + latest_commit_hash
			starting_commit_hash = latest_commit_hash
		else:
			print 'No attack surface change'
	else:
		print 'Latest commit is still: ' + starting_commit_hash
	time.sleep(10)


# git_diff_attack_surface = compare_git_commits(repo_path, branch, start_commit, end_commit)
# print 'Differences between git commit: ' + start_commit + ' and commit: ' + end_commit
# print 'Added attack surface: ' + ', '.join(git_diff_attack_surface.added)
# print 'Deleted attack surface: ' + ', '.join(git_diff_attack_surface.deleted)
# print 'Added percent: ' + str(git_diff_attack_surface.added_percent())
# print 'Deleted percent: ' + str(git_diff_attack_surface.deleted_percent())
