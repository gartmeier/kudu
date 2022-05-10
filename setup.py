from setuptools import find_packages, setup

from kudu import __author__, __email__, __version__

setup(
    name='kudu',
    author=__author__,
    author_email=__email__,
    version=__version__,
    description='A deployment command line program in Python.',
    url='https://github.com/torfeld6/kudu',
    license='BSD',
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Utilities',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    keywords='cli',
    packages=find_packages(),
    install_requires=[
        'requests>=2.25.1',
        'PyYAML>=5.4.1,<6.0.0',
        'watchdog>=0.10.4,<1.0.0',
        'click>=7.1.2,<8.0.0',
    ],
    entry_points={
        'console_scripts': ['kudu = kudu.__main__:cli',],
    },
)
