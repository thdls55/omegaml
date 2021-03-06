import logging
import os
import sys
import threading

import callable_pip as cpip
from tee import tee

sync_lock = threading.Lock()

logger = logging.getLogger(__name__)

def build_sdist(src, distdir):
    from distutils.core import run_setup
    # save argv. distutils run_setup changes argv and fails at restoring properly
    save_argv = list(sys.argv)
    # block any other thread from executing since we're changing cwd and sys.argv
    with sync_lock, tee.StdoutTee('build_sdist.out', 'w', 2), \
         tee.StderrTee('build_sdist.err', 'w', 2):
        # make sure no other processing is executing while we change the working directory for setup.py
        cwd = os.getcwd()
        sys.stdout.errors = None
        sys.stderr.errors = None
        try:
            os.chdir(src)
            setup_path = os.path.join(src, 'setup.py')
            sdist = run_setup(setup_path, script_args=['sdist', '--dist-dir', distdir])
        finally:
            # restore cwd
            os.chdir(cwd)
            # restore sys argv
            for i ,v in enumerate(save_argv):
                sys.argv[i] = v
            if len(sys.argv) > len(save_argv):
                del sys.argv[len(save_argv):]
    return sdist


def install_package(src, dst):
    cpip.main('install',
              src,
              '--force-reinstall',
              '--upgrade',
              '--target', dst)


def load_from_path(name, path):
    import importlib
    sys.path.insert(0, path)
    try:
        if name in sys.modules:
            del sys.modules[name]
        if name in globals():
            del globals()[name]
        mod = importlib.import_module(name)
    finally:
        sys.path.remove(path)
    return mod


def install_and_import(pkgfilename, package, installdir):
    install_package(pkgfilename, installdir)
    mod = load_from_path(package, installdir)
    return mod


if __name__ == '__main__':
    basepath = os.path.join(os.path.dirname(__file__), '..')
    pkgpath = os.path.join(basepath, 'demo/helloworld')
    build_sdist(pkgpath)

    pkgfilename = os.path.join(basepath, 'demo/helloworld/dist/helloworld-1.0.tar.gz')
    installdir = '/tmp/xyz'
    install_and_import(pkgfilename, 'helloworld', installdir)

    import helloworld

    helloworld.hello()
