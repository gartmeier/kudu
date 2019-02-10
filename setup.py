from setuptools import setup

from kudu import __author__
from kudu import __email__
from kudu import __version__

setup(
    name='kudu',
    version=__version__,
    description='A deployment command line program in Python.',
    url='https://github.com/torfeld6/kudu-cli',
    author=__author__,
    author_email=__email__,
    license='BSD',
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Utilities',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    keywords='cli',
    install_requires=['requests', 'PyYAML', 'GitPython', 'watchdog', 'click', 'anyconfig'],
    entry_points={
        'console_scripts': [
            'kudu = kudu.__main__:main',
        ],
    },
)
