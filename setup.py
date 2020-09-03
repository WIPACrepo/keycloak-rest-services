#!/usr/bin/env python
"""Setup."""

import glob
import os
import re
import sys

PACKAGE = "keycloak-rest-services"

if sys.version_info < (3, 6):
    print(f"ERROR: {PACKAGE} requires at least Python 3.6+ to run.")
    sys.exit(1)

try:
    # Use setuptools if available, for install_requires (among other things).
    import setuptools
    from setuptools import setup
except ImportError:
    setuptools = None
    from distutils.core import setup

kwargs = {}

current_path = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(current_path, "__init__.py")) as f:
    for line in f.readlines():
        if "__version__" in line:
            PATTERN = r"""__version__ = ('|")(?P<v>.+)('|")"""
            kwargs["version"] = re.match(PATTERN, line).groupdict()["v"]
            break
    else:
        raise Exception("cannot find __version__")

with open(os.path.join(current_path, "README.md")) as f:
    kwargs["long_description"] = f.read()
    kwargs["long_description_content_type"] = "text/markdown"

if setuptools is not None:
    # If setuptools is not available, you're on your own for dependencies.
    install_requires = []
    dependency_links = []
    with open(os.path.join(current_path, "requirements.txt")) as f:
        for line in f.readlines():
            # GitHub Dependency
            if m := re.match(r"(-e git:|-e git\+|git:|git\+)(?P<src>.*)", line):
                src = m.groupdict()["src"]
                if m := re.match(r"(?P<url>.*)(?P<egg>#egg=)(?P<pkg>.*)", src):
                    # add tarball master link
                    tarball_link = f"{m['url']}/tarball/master{m['egg']}{m['pkg']}"
                    dependency_links.append(tarball_link)
                    # add package name
                    install_requires.append(m["pkg"])
                else:
                    print("Dependency to a git repository should have the format:")
                    print("git+[ssh|https]://git@github.com/xxxx/xxxx#egg=package_name")
            # Don't Add PyTests
            elif "pytest" in line:
                continue
            # PyPI Dependency
            else:
                install_requires.append(line)

    kwargs["install_requires"] = install_requires
    kwargs["dependency_links"] = dependency_links
    kwargs["zip_safe"] = False


setup(
    name=PACKAGE,
    scripts=glob.glob("bin/*"),
    packages=["krs", "resources"],
    package_data={
        # data files need to be listed both here (which determines what gets
        # installed) and in MANIFEST.in (which determines what gets included
        # in the sdist tarball)
        # 'rest_utils.server':['data/etc/*','data/www/*','data/www_templates/*'],
    },
    author="IceCube Collaboration",
    author_email="developers@icecube.wisc.edu",
    url=f"https://github.com/WIPACrepo/{PACKAGE}",
    license=f"https://github.com/WIPACrepo/{PACKAGE}/blob/master/LICENSE",
    description="Services surrounding KeyCloak, that use the REST API to read/update state",
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 3 - Alpha",
        "Operating System :: POSIX :: Linux",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: System :: Distributed Computing",
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    **kwargs,
)
