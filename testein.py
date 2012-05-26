#!/usr/bin/env python

"""
Run EIN test suite
"""

import os
ZEROEIN_ROOT = os.path.dirname(__file__)
ZEROEIN_EL = os.path.join(ZEROEIN_ROOT, 'zeroein.el')


def run(command):
    from subprocess import Popen, PIPE, STDOUT
    proc = Popen(command, stdout=PIPE, stderr=STDOUT)
    return proc


def zeroeindir(*path):
    return os.path.join(ZEROEIN_ROOT, *path)


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
        command.extend(['-L', zeroeindir('ein'),
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


def run_ein_test(unit_test, func_test, **kwds):
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
    parser = ArgumentParser(description=__doc__.split()[1])
    parser.add_argument('--emacs', '-e', default='emacs',
                        help='Emacs executable.')
    parser.add_argument('--no-batch', '-B', default=True,
                        dest='batch', action='store_false')
    parser.add_argument('--debug-on-error', '-d', default=False,
                        action='store_true')
    parser.add_argument('--no-func-test', '-F', default=True,
                        dest='func_test', action='store_false')
    parser.add_argument('--no-unit-test', '-U', default=True,
                        dest='unit_test', action='store_false')
    args = parser.parse_args()
    sys.exit(run_ein_test(**vars(args)))


if __name__ == '__main__':
    main()
