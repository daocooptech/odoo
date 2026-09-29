# -*- coding: utf-8 -*-
"""DAO COOPTECH build of Odoo: gate before tagging a version.

Fails (exit 1) when the tree still has:
  * an Odoo S.A. service endpoint or an import of a removed service module
    in code that runs (tests, i18n and comments-only files are skipped);
  * fewer copyright notices than upstream in the modules we kept
    (LGPL-3 / GPL-3 section 4: notices must be preserved);
  * something that looks like a secret.

    python .coop/check.py [--upstream <ref>]   # default ref: df0149e3
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coop_services as cs  # noqa: E402

NOTICE = re.compile(r'Copyright|Part of Odoo')
SECRET = re.compile(r'BEGIN [A-Z ]*PRIVATE KEY|aws_secret_access_key|ghp_[A-Za-z0-9]{30,}')


def git(*args):
    return subprocess.check_output(['git'] + list(args), cwd=cs.ROOT).decode('utf-8', 'replace')


def main(argv):
    upstream = argv[argv.index('--upstream') + 1] if '--upstream' in argv else 'df0149e3'
    bad = 0
    mods = cs.manifests()

    for name, (path, _deps) in sorted(mods.items()):
        for fpath, lineno, text in cs.service_hits(path):
            stripped = text.lstrip()
            if stripped.startswith(('#', '//', '*', '<!--')):
                continue
            print('SERVICE %s:%d %s' % (os.path.relpath(fpath, cs.ROOT), lineno, text))
            bad += 1

    # Imports of removed modules from kept ones: account imported base_vat
    # without declaring it, and the registry failed to load (29.09 on a copy
    # of production). Declared dependencies are not enough to catch this.
    listed = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'removed-modules.txt')
    if os.path.exists(listed):
        with open(listed, encoding='utf-8') as fh:
            removed = {l.split()[0] for l in fh if l.strip() and not l.startswith('#')}
        removed -= set(mods)
        if removed:
            names = '|'.join(sorted(map(re.escape, removed)))
            imp = re.compile(r'''(?:odoo[.]addons[.](%s)(?![a-z0-9_])|["']@(%s)/)''' % (names, names))
            for name, (path, _deps) in sorted(mods.items()):
                for fpath in cs.module_files(path):
                    with open(fpath, encoding='utf-8', errors='ignore') as fh:
                        for lineno, line in enumerate(fh, 1):
                            if imp.search(line) and not line.lstrip().startswith(('#', '//')):
                                print('IMPORT %s:%d %s' % (os.path.relpath(fpath, cs.ROOT), lineno, line.strip()[:140]))
                                bad += 1

    # Whole tree minus the directories of removed modules: a notice may only
    # disappear together with the module that carried it.
    gone = tuple(line.rstrip('/') + '/' for line in
                 git('ls-tree', '-d', '--name-only', upstream, 'addons/', 'odoo/addons/').split()
                 if not os.path.isfile(os.path.join(cs.ROOT, line, '__manifest__.py')))

    def count(*ref):
        out = subprocess.run(['git', 'grep', '-c', '-E', 'Copyright|Part of Odoo'] + list(ref),
                             cwd=cs.ROOT, capture_output=True).stdout.decode('utf-8', 'replace')
        total = 0
        for line in out.splitlines():
            parts = line.split(':')
            path, n = parts[-2], parts[-1]
            if not path.startswith(gone):
                total += int(n)
        return total

    up, now = count(upstream), count()
    print('copyright notices in kept modules: upstream %d, now %d' % (up, now))
    if now < up:
        print('NOTICE LOST: %d copyright lines removed' % (up - now))
        bad += 1

    for f in git('ls-files').split('\n'):
        if not f or '/tests/' in f or f.startswith('.coop/') or not f.endswith(('.py', '.xml', '.js', '.conf', '.cfg', '.env', '.txt')):
            continue
        full = os.path.join(cs.ROOT, f)
        try:
            with open(full, encoding='utf-8', errors='ignore') as fh:
                for lineno, line in enumerate(fh, 1):
                    if SECRET.search(line):
                        print('SECRET? %s:%d' % (f, lineno))
                        bad += 1
        except OSError:
            pass

    print('check: %s' % ('FAILED, %d problem(s)' % bad if bad else 'clean'))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
