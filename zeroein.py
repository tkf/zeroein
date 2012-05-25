#!/usr/bin/env python

"""
Zero setup Emacs IPython Notebook client
"""


def zeroein(emacs):
    import subprocess
    import os
    elisp = os.path.join(os.path.dirname(__file__), 'zeroein.el')
    subprocess.Popen([emacs, '-Q', '-l', elisp])


def main():
    from argparse import ArgumentParser
    parser = ArgumentParser(description=__doc__.split()[1])
    parser.add_argument('--emacs', '-e', default='emacs',
                        help='Emacs executable.')
    args = parser.parse_args()
    zeroein(**vars(args))


if __name__ == '__main__':
    main()
