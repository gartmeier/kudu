# This is purely the result of trial and error.

from setuptools import setup, find_packages

import kudu

install_requires = [
    'requests>=2.21.0',
    'GitPython>=2.1.11',
    'paramiko>=2.4.2',
    'watchdog>=0.9.0'
]

# bdist_wheel
extras_require = {
    # http://wheel.readthedocs.io/en/latest/#defining-conditional-dependencies
    'python_version == "3.0" or python_version == "3.1"': ['argparse>=1.2.1'],
}


def long_description():
    return ''


setup(
    name='kudu',
    version=kudu.__version__,
    author=kudu.__author__,
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'kudu = kudu.__main__:main',
        ],
    },
    extras_require=extras_require,
    install_requires=install_requires
)
