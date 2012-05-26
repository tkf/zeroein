#!/usr/bin/env python

"""
Zero setup Emacs IPython Notebook client
"""

import os
ZEROEIN_ROOT = os.path.dirname(__file__)


class BaseTask(object):

    cwd = ZEROEIN_ROOT
    parents = []
    pconfig = {}
    done = False

    def run(self):
        self.start()
        self.wait()

    def start(self):
        if self.done:
            return
        tasks = []
        for p in self.parents:
            tasks.append(p(**self.pconfig.get(p, {})))
        for t in tasks:
            t.start()
        for t in tasks:
            t.wait()

    def wait(self):
        pass


class BaseBlockingTask(BaseTask):

    def start(self):
        if self.done:
            return
        for p in self.parents:
            t = p(**self.pconfig.get(p, {}))
            t.start()
            t.wait()


class BaseCommandTask(BaseTask):

    command = []
    proc = None

    def start(self):
        import subprocess
        super(BaseCommandTask, self).start()
        self.proc = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.cwd or None)

    def wait(self):
        if self.proc:
            if self.proc.wait() != 0:
                print self.proc.stdout.read()
                print self.proc.stderr.read()
                raise RuntimeError("An error occurred while running {0}"
                                   .format(self.command))


class BaseGitModuleTask(BaseCommandTask):

    subcommand = None

    def __init__(self, reponame):
        self.reponame = reponame

    @property
    def command(self):
        return ['git', 'submodule', self.subcommand, self.reponame]


class GitModuleInit(BaseGitModuleTask):
    subcommand = 'init'


class GitModuleUpdate(BaseGitModuleTask):
    subcommand = 'update'


class BaseModuleTask(BaseBlockingTask):

    reponame = None
    parents = [GitModuleInit, GitModuleUpdate]

    def __init__(self):
        super(BaseModuleTask, self).__init__()
        config = {'reponame': self.reponame}
        self.pconfig = {GitModuleInit: config, GitModuleUpdate: config}
        if os.path.isdir(os.path.join(self.cwd, self.reponame, '.git')):
            self.done = True

    def start(self):
        if not self.done:
            print "Preparing {0}".format(self.reponame)
        super(BaseModuleTask, self).start()

    def wait(self):
        super(BaseModuleTask, self).wait()
        print "Preparing {0}... Done".format(self.reponame)


def make_module_task(_reponame):
    class Task(BaseModuleTask):
        reponame = _reponame
    return Task


class PrepareModulesTask(BaseTask):

    parents = map(
        make_module_task,
        ["fuzzy", "pos-tip", "smartrep", "auto-complete", "python",
         "websocket", "markdown-mode", "nxhtml", "popup", "ein"])


class ZeroEINTask(BaseCommandTask):

    parents = [PrepareModulesTask]

    def __init__(self, command):
        self.command = command

    def start(self):
        super(ZeroEINTask, self).start()
        print "Starting Emacs..."


def zeroein(emacs):
    elisp = os.path.join(ZEROEIN_ROOT, 'zeroein.el')
    task = ZeroEINTask([emacs, '-Q', '-l', elisp])
    task.start()


def main():
    from argparse import ArgumentParser
    parser = ArgumentParser(description=__doc__.split()[1])
    parser.add_argument('--emacs', '-e', default='emacs',
                        help='Emacs executable.')
    args = parser.parse_args()
    zeroein(**vars(args))


if __name__ == '__main__':
    main()
