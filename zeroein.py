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

    def gene(self):
        ptasks = []
        for p in self.parents:
            ptasks.append(p(**self.pconfig.get(p, {})).start())
        while ptasks:
            nexttasks = []
            for t in ptasks:
                try:
                    yield t.next()
                except StopIteration:
                    pass
                else:
                    nexttasks.append(t)
            ptasks = nexttasks

    def start(self):
        if self.done:
            self.tasks = iter([])
        else:
            self.tasks = self.gene()
        return self.tasks

    def wait(self):
        for t in self.tasks:
            pass


class BaseBlockingTask(BaseTask):

    def gene(self):
        for p in self.parents:
            t = p(**self.pconfig.get(p, {}))
            t.start()
            t.wait()
            yield t


class BaseCommandTask(BaseTask):

    command = []
    proc = None

    def gene(self):
        import subprocess
        for t in super(BaseCommandTask, self).gene():
            yield t
        self.proc = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.cwd or None)
        yield self.proc
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
        return super(BaseModuleTask, self).start()

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
        print "Starting Emacs..."
        return super(ZeroEINTask, self).start()


def zeroein(emacs):
    elisp = os.path.join(ZEROEIN_ROOT, 'zeroein.el')
    task = ZeroEINTask([emacs, '-Q', '-l', elisp])
    task.run()


def main():
    from argparse import ArgumentParser
    parser = ArgumentParser(description=__doc__.split()[1])
    parser.add_argument('--emacs', '-e', default='emacs',
                        help='Emacs executable.')
    args = parser.parse_args()
    zeroein(**vars(args))


if __name__ == '__main__':
    main()
