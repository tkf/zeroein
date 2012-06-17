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

    def iter_parents(self):
        for p in self.parents:
            yield p(**self.pconfig.get(p, {}))

    def gene(self):
        self.on_start()
        ptasks = []
        for t in self.iter_parents():
            ptasks.append(t.start())
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
        self.on_current_task()
        for t in self.current_task():
            yield t
        self.on_close()

    def current_task(self):
        return iter([])

    def start(self):
        if self.done:
            self.tasks = iter([])
        else:
            self.tasks = self.gene()
        return self.tasks

    def wait(self):
        for t in self.tasks:
            pass

    def on_start(self):
        pass

    def on_current_task(self):
        pass

    def on_close(self):
        pass


class BaseListConfigTask(BaseTask):

    def iter_parents(self):
        import itertools
        pconfig = itertools.chain(self.pconfig, itertools.repeat({}))
        for (p, c) in zip(self.parents, pconfig):
            yield p(**c)


class BaseBlockingTask(BaseTask):

    def gene(self):
        self.on_start()
        for t in self.iter_parents():
            t.start()
            t.wait()
            yield t
        for t in self.current_task():
            yield t
        self.on_close()


class BaseCommandTask(BaseTask):

    command = []
    proc = None

    def current_task(self):
        import subprocess
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


class ModuleTask(BaseBlockingTask):

    parents = [GitModuleInit, GitModuleUpdate]

    def __init__(self, reponame):
        super(ModuleTask, self).__init__()
        self.reponame = reponame
        config = {'reponame': self.reponame}
        self.pconfig = {GitModuleInit: config, GitModuleUpdate: config}
        if os.path.isdir(os.path.join(self.cwd, self.reponame, '.git')):
            self.done = True
            print "{0} is ready".format(self.reponame)

    def on_start(self):
        if not self.done:
            print "Preparing {0}".format(self.reponame)

    def on_close(self):
        print "Preparing {0}... Done".format(self.reponame)


class PrepareModulesTask(BaseListConfigTask):

    pconfig = map(
        lambda x: {'reponame': x},
        ["fuzzy", "pos-tip", "smartrep", "auto-complete", "python",
         "websocket", "markdown-mode", "nxhtml", "popup", "ein"])
    parents = [ModuleTask] * len(pconfig)


class ZeroEINTask(BaseCommandTask):

    parents = [PrepareModulesTask]
    cwd = None

    def __init__(self, command):
        self.command = command

    def on_current_task(self):
        print "Starting Emacs..."


def zeroein(emacs):
    elisp = os.path.join(ZEROEIN_ROOT, 'zeroein.el')
    command = [emacs, '-Q', '-l', elisp, '-f', 'ein:notebooklist-open']
    task = ZeroEINTask(command)
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
