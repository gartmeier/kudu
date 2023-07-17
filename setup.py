from setuptools import find_packages, setup

from kudu import __author__, __email__, __version__

setup(
    name="kudu",
    author=__author__,
    author_email=__email__,
    version=__version__,
    description="A deployment command line program in Python.",
    url="https://github.com/torfeld6/kudu",
    license="BSD",
    classifiers=[
        "Intended Audience :: Developers",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="cli",
    packages=find_packages(),
    install_requires=[
        "requests",
        "PyYAML",
        "watchdog",
        "click",
    ],
    entry_points={
        "console_scripts": [
            "kudu = kudu.__main__:cli",
        ],
    },
)
