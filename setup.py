from setuptools import setup

from rotten_bites import __version__

DOWNLOAD_URL = ('https://github.com/philipbl/rotten_bites/archive/'
                '{}.zip'.format(__version__))

REQUIRES = [
    'click==6.6',
    'pathspec==0.3.4',
]

setup(
    name='rotten_bites',
    version=__version__,
    author='Philip Lundrigan',
    author_email='philipbl@cs.utah.edu',
    download_url=DOWNLOAD_URL,
    install_requires=REQUIRES,
    description='A tool for detecting bit rot in files.',
    entry_points={
        'console_scripts': [
            'rotten_bites = rotten_bites.__main__:main'
        ]
    },
)
