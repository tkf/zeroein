#!/usr/bin/env python

"""
Run EIN test suite
"""

import os
import glob

ZEROEIN_ROOT = os.path.dirname(__file__)
ZEROEIN_EL = os.path.join(ZEROEIN_ROOT, 'zeroein.el')


def run(command):
    from subprocess import Popen, PIPE, STDOUT
    proc = Popen(command, stdout=PIPE, stderr=STDOUT)
    return proc


def zeroeindir(*path):
    return os.path.join(ZEROEIN_ROOT, *path)


def einlispdir(*path):
    return zeroeindir('ein', 'lisp', *path)


def eintestdir(*path):
    return zeroeindir('ein', 'tests', *path)


class TestRunner(object):

    def __init__(self, **kwds):
        self.__dict__.update(kwds)
        self.batch = self.batch and not self.debug_on_error

        fmtdata = self.__dict__.copy()
        fmtdata.update(
            emacsname=os.path.basename(self.emacs),
            testname=os.path.splitext(self.testfile)[0],
            modename='batch' if self.batch else 'interactive',
        )
        self.lispvars = {
            'ein:testing-dump-file-log':
            '{testname}_log_{modename}_{emacsname}.log'.format(**fmtdata),
            'ein:testing-dump-file-messages':
            '{testname}_messages_{modename}_{emacsname}.log'.format(**fmtdata),
        }

    def bind_lispvars(self):
        command = []
        for (k, v) in self.lispvars.iteritems():
            command.extend([
                '--eval', '(setq {0} "{1}")'.format(k, v)])
        return command

    def command(self):
        command = [self.emacs, '-Q'] + self.bind_lispvars()

        if self.batch:
            command.append('-batch')
        if self.debug_on_error:
            command.extend(['-f', 'toggle-debug-on-error'])

        # load modules
        if self.load_ert:
            ertdir = zeroeindir('ert', 'lisp', 'emacs-lisp')
            command.extend([
                '-L', ertdir,
                # Load `ert-run-tests-batch-and-exit`:
                '-l', os.path.join(ertdir, 'ert-batch.el'),
                # Load `ert-run-tests-interactively`:
                '-l', os.path.join(ertdir, 'ert-ui.el'),
             ])
        for path in self.load_path:
            command.extend(['-L', path])
        for path in self.load:
            command.extend(['-l', path])
        command.extend(['-L', einlispdir(),
                        '-L', zeroeindir('websocket'),
                        '-L', zeroeindir('auto-complete'),
                        '-L', zeroeindir('popup'),
                        '-L', eintestdir(),
                        '-l', eintestdir(self.testfile)])

        # do the test
        if self.batch:
            command.extend(['-f', 'ert-run-tests-batch-and-exit'])
        else:
            command.extend(['--eval', "(ert 't)"])
        return command

    def make_process(self):
        print "Start test {0}".format(self.testfile)
        self.proc = run(self.command())
        return self.proc

    def report(self):
        if self.proc.wait() != 0:
            print "{0} failed".format(self.testfile)
            print self.proc.stdout.read()
            self.failed = True
        else:
            print "{0} OK".format(self.testfile)
            self.failed = False
        return int(self.failed)

    def run(self):
        self.make_process()
        return self.report()


def remove_elc():
    files = glob.glob(einlispdir("*.elc")) + glob.glob(eintestdir("*.elc"))
    map(os.remove, files)
    print "Removed {0} elc files".format(len(files))


def construct_command(args):
    """
    Construct command as a string given a list of arguments.
    """
    command = []
    escapes = set(' ()')
    for a in args:
        if set(a) & escapes:
            command.append(repr(str(a)))  # hackish way to escape
        else:
            command.append(a)
    return " ".join(command)


def run_ein_test(unit_test, func_test, clean_elc, dry_run, **kwds):
    if clean_elc and not dry_run:
        remove_elc()
    if unit_test:
        unit_test_runner = TestRunner(testfile='test-load.el', **kwds)
        if dry_run:
            print construct_command(unit_test_runner.command())
        elif unit_test_runner.run() != 0:
            return 1
    if func_test:
        func_test_runner = TestRunner(testfile='func-test.el', **kwds)
        if dry_run:
            print construct_command(func_test_runner.command())
        elif func_test_runner.run() != 0:
            return 1
    return 0


def main():
    import sys
    from argparse import ArgumentParser
    parser = ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument('--emacs', '-e', default='emacs',
                        help='Emacs executable.')
    parser.add_argument('--load-path', '-L', default=[], action='append',
                        help="add a directory to load-path. "
                        "can be specified multiple times.")
    parser.add_argument('--load', '-l', default=[], action='append',
                        help="load lisp file before tests. "
                        "can be specified multiple times.")
    parser.add_argument('--load-ert', default=False, action='store_true',
                        help="load ERT from git submodule. "
                        "you need to update git submodule manually "
                        "if ert/ directory does not exist yet.")
    parser.add_argument('--no-batch', '-B', default=True,
                        dest='batch', action='store_false',
                        help="start interactive session.")
    parser.add_argument('--debug-on-error', '-d', default=False,
                        action='store_true',
                        help="set debug-on-error to t and start "
                        "interactive session.")
    parser.add_argument('--no-func-test', '-F', default=True,
                        dest='func_test', action='store_false',
                        help="do not run functional test.")
    parser.add_argument('--no-unit-test', '-U', default=True,
                        dest='unit_test', action='store_false',
                        help="do not run unit test.")
    parser.add_argument('--clean-elc', '-c', default=False,
                        action='store_true',
                        help="remove *.elc files in ein/lisp and "
                        "ein/tests directories.")
    parser.add_argument('--dry-run', default=False,
                        action='store_true',
                        help="Print commands to be executed.")
    args = parser.parse_args()
    sys.exit(run_ein_test(**vars(args)))


if __name__ == '__main__':
    main()
