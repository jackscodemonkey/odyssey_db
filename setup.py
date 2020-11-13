from setuptools import setup, find_packages
from odyssey_db import __version__, __release__

cmdclass = {}
try:
    from sphinx.setup_command import BuildDoc
    cmdclass['build_sphinx'] = BuildDoc
except ImportError:
    print("Warning: sphinx is not available, not building docs.")

with open('README.rst') as file:
    long_description = file.read()

version = __version__
release = __release__
name = 'odyssey-db'

setup(
    name=name,
    version=release,
    packages=find_packages(),
    url='https://github.com/jackscodemonkey/sphinx-sql',
    license='GPU',
    author='Marcus Robb',
    description="Database first migration manager.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    install_requires=[
        'sphinx-sql',
	'sphinx-argparse',
	'pytest',
    'pytest-mock',
    'psycopg2-binary',
    ],
    include_package_data=True,
    cmdclass=cmdclass,
    command_options={
        'build_sphinx': {
            'project': ('setup.py', name),
            'version': ('setup.py', version),
            'release': ('setup.py', release),
            'source_dir': ('setup.py', 'docs/source'),
            'build_dir': ('setup.py', 'docs/build')
        }
    },
    entry_points={
        "console_scripts": [
            "odyssey = odyssey_db.odyssey_db:main"
        ]
    }
)
