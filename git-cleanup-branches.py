#!/usr/bin/env python3
import re
import subprocess
import sys
import argparse



parser = argparse.ArgumentParser(description='delete stale branches')
parser.add_argument('--remote', type=str, default='origin',
                    help='name of the remote to sync with')
parser.add_argument('--all', dest='delete_all', action='store_const',
                    const=True, default=False,
                    help='cleanup all stalled branches')

args = parser.parse_args()
remote_name = args.remote
current_branch = subprocess.check_output(
        ['git','rev-parse','--abbrev-ref', 'HEAD']
        ).decode(encoding="utf-8").strip()


def parse_vv():
    r = re.compile(r'^\s*\*?\s*(\S+)[^[]+\[([^]]+)\]')
    b = subprocess.check_output(['git','branch','-vv'])
    s = b.decode(encoding="utf-8")
    for line in s.splitlines():
        m = r.match(line)
        if m is not None:
            yield {'local': m[1], 'remote':m[2]}

def parse_prune():
    r = re.compile(r'^\s*\*?\s*\[would prune\] (\S+)')
    b = subprocess.check_output(['git','remote', 'prune', remote_name, '--dry-run'])
    s = b.decode(encoding="utf-8")
    for line in s.splitlines():
        m = r.match(line)
        if m is not None:
            yield m[1]

def parse_merged():
    r = re.compile(r'^\s*([^*]+)')
    b = subprocess.check_output(['git','branch', '--merged'])
    s = b.decode(encoding="utf-8")
    for line in s.splitlines():
        m = r.match(line)
        if m is not None:
            yield m[1]

def yes_or_no(question):
    reply = str(input(question+' (y/N): ')).lower().strip()
    if len(reply) == 1 and reply[0] == 'y':
        return True
    if len(reply) == 1 and reply[0] == 'n':
        return False
    if len(reply) == 0:
        return False
    else:
        return yes_or_no("please enter y or n")


pb = [x for x in parse_prune()]
lb = [x['local'] for x in parse_vv() if x['remote'] in pb]
mb = [x for x in parse_merged() ]


bd = []
bk = []
for item in lb:
    to_delete = args.delete_all
    if to_delete is False:
        to_delete = yes_or_no(
            '  prune: {} was deleted in {}. delete?'.format(
                item,
                remote_name,
            )
        )
    if to_delete:
        bd.append({'branch':item, 'reason':'prune '+remote_name})
    else:
        bk.append(item)


for item in [x for x in mb if x not in lb]:
    to_delete = args.delete_all
    if to_delete is False:
        to_delete = yes_or_no(
            'merged: {} was already merged to {}. delete?'.format(
                item,
                current_branch,
            )
        )
    if to_delete:
        bd.append({'branch':item, 'reason':'merged into '+current_branch})
    else:
        bk.append(item)


if len(bk) != 0:
    s = '\n- '.join(bk)
    print('\nlocal branches to keep:\n-', s)

if len(bd) == 0:
    sys.exit(0)

if len(bd) != 0:
    s = '\n- '.join('{} ({})'.format(x['branch'], x['reason'])
            for x in bd)
    print('\nlocal branches to delete:\n-', s)

if yes_or_no(
    '\nif you will delete those branches you will'
    '\nnot be able to restore them from remote.'
    '\ncontinue?') is False:
    sys.exit(0)

for item in bd:
    subprocess.call(["git","branch","-D", item['branch']])

if len([x for x in bk if x in lb]) > 0:
    if not yes_or_no(
        '\nstale branches in {0} is about to be pruned.'
        '\nif you will press y now it would be impossible'
        '\nto link your stale local branches to stale'
        '\nremote branches in {0}.'
        '\n\nprune remote {0}?'.format(remote_name)):
        sys.exit(0)

subprocess.call(["git","remote", "prune", remote_name])
