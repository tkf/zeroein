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


def eindir(*path):
    return zeroeindir('ein', 'lisp', *path)


def testdir(*path):
    return zeroeindir('ein', 'tests', *path)


class TestRunner(object):

    def __init__(self, **kwds):
        self.__dict__.update(kwds)

    def command(self):
        command = [self.emacs, '-Q']
        batch = self.batch and not self.debug_on_error
        if batch:
            command.append('-batch')
        if self.debug_on_error:
            command.extend(['-f', 'toggle-debug-on-error'])
        if self.load_ert:
            ertdir = zeroeindir('ert', 'lisp', 'emacs-lisp')
            command.extend(
                ['-L', ertdir, '-l', os.path.join(ertdir, 'ert-batch.el')])
        for path in self.load_path:
            command.extend(['-L', path])
        for path in self.load:
            command.extend(['-l', path])
        command.extend(['-L', eindir(),
                        '-L', zeroeindir('websocket'),
                        '-L', testdir(),
                        '-l', testdir(self.testfile)])
        if batch:
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
    files = glob.glob(eindir("*.elc")) + glob.glob(testdir("*.elc"))
    map(os.remove, files)
    print "Removed {0} elc files".format(len(files))


def run_ein_test(unit_test, func_test, clean_elc, **kwds):
    if clean_elc:
        remove_elc()
    if unit_test:
        unit_test_runner = TestRunner(testfile='test-load.el', **kwds)
        if unit_test_runner.run() != 0:
            return 1
    if func_test:
        func_test_runner = TestRunner(testfile='func-test.el', **kwds)
        if func_test_runner.run() != 0:
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
    args = parser.parse_args()
    sys.exit(run_ein_test(**vars(args)))


if __name__ == '__main__':
    main()
