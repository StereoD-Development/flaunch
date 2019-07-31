"""
git things
"""
from __future__ import absolute_import

import subprocess

from . import utils

def clone_repo(git_url):
    """
    clone a repository
    :param git_url: url to the remote repository
    :return: Boolean of success
    """
    if utils.run_(['git', 'clone', git_url]) != 0:
        logging.error('Failed to clone repository')
        return False
    return True


def fetch(tags=False):
    """
    Stash any changes we currently have
    """
    command = ['git', 'fetch']
    if tags:
        command += ['--tags']
    if utils.run_(command) != 0:
        logging.error('Failed to fetch updates')
        return False
    return True


def stash():
    """
    Stash any changes we currently have
    """
    if utils.run_(['git', 'stash', '--all']) != 0:
        logging.error('Failed to stash repository')
        return False
    return True


def checkout(branch=None, tag=None):
    """
    Checkout a branch or a tag
    :param branch: If this isn't None, we checkout this branch
    :param tag: If this isn't None and branch is None, we checkout this tag
    """
    command = ['git', 'checkout']
    if branch is not None:
        # full_branch_target = 'origin/' + branch if '/' not in branch else '/'
        # command.extend(['--track', full_branch_target])
        command.extend([branch])

    elif tag is not None:
        if not fetch(tags=True):
            return False
        command.extend([tag])

    if utils.run_(command) != 0:
        logging.error('Failed to checkout {}'.format(branch or tag))
        return False
    return True


def git_hash(branch_or_tag):
    """
    Obtain the git hash for a specific branch or tag
    :param branch_or_tag: str
    :return: str
    """
    try:
        data = subprocess.check_output(['git', 'rev-parse', branch_or_tag])
    except subprocess.CallProcessError as e:
        logging.critical('Failed to locate proper hash for {}'.format(branch_or_tag))
        raise
    return data.decode('utf-8').strip()


def tag(tag_name, code_hash):
    """
    Tag the code at a specific commit hash .
    :param code_hash: The hash that we're placing this tag at
    :return: bool
    """
    addon = [code_hash] if code_hash else []

    if utils.run_(['git', 'tag', '-a', tag_name] + addon) != 0:
        logging.error('Failed to tag {}'.format(tag_name))
        return False
    return True


def push_tag(tag_name, remote='origin'):
    """
    Push the tag to our git repository
    :param tag_name: The verison that we're pushing up
    :param remote: The remote to use when pushing
    :return: bool
    """
    if utils.run_(['git', 'push', remote, tag_name]) != 0:
        logging.error('Failed to push tag {}'.format(tag_name))
        return False
    return True
