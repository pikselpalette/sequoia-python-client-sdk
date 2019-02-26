#!/usr/bin/env python3
import sys

try:
    import clinner_piksel_extensions
    from clinner.run import Main
except ImportError:
    import importlib
    import site
    import subprocess
    subprocess.call(['pip', 'install', '-U', 'clinner', 'clinner_piksel_extensions'])
    importlib.reload(site)

    import clinner_piksel_extensions
    from clinner.run import Main


class Build(Main):
    commands = (
        'clinner_piksel_extensions.python.clean.clean',
        'clinner_piksel_extensions.python.prepare.prepare',
        'clinner_piksel_extensions.python.virtualenv.virtualenv',
        'clinner_piksel_extensions.python.test.debugtest',
        'clinner_piksel_extensions.python.test.prospector',
        'clinner_piksel_extensions.python.test.pytest',
        'clinner_piksel_extensions.python.test.test',
        'clinner_piksel_extensions.python.package.package',
        'clinner_piksel_extensions.piksel.upload_artifact.upload_artifact',
        'clinner_piksel_extensions.piksel.download_artifact.download_artifact',
        'clinner_piksel_extensions.python.deploy.deploy',
        'clinner_piksel_extensions.python.install.install',
        'clinner_piksel_extensions.python.bump.bump'
    )


def main():
    return Build().run()


if __name__ == '__main__':
    sys.exit(main())
