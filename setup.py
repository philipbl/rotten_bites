from setuptools import setup, find_packages

try:
    from pypandoc import convert
    read_md = lambda f: convert(f, 'rst')
except ImportError:
    print("warning: pypandoc module not found, could not convert Markdown to RST")
    read_md = lambda f: open(f, 'r').read()

VERSION = '1.0.0'
DOWNLOAD_URL = ('https://github.com/philipbl/rotten_bites/archive/'
                '{}.zip'.format(VERSION))
PACKAGES = find_packages(exclude=['tests', 'tests.*'])
REQUIRES = [
    'click==6.6',
    'pathspec==0.4.0',
]

setup(
    name='rotten_bites',
    version=VERSION,
    license='MIT License',
    author='Philip Lundrigan',
    author_email='philipbl@cs.utah.edu',
    download_url=DOWNLOAD_URL,
    install_requires=REQUIRES,
    packages=PACKAGES,
    include_package_data=True,
    test_suite='tests',
    zip_safe=False,
    url='https://github.com/philipbl/rotten_bites',
    description='A tool for detecting bit rot in files.',
    long_description=read_md('README.md'),
    entry_points={
        'console_scripts': [
            'rotten_bites = rotten_bites.__main__:main'
        ]
    },
    classifiers=[
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.4',
    ],
)
