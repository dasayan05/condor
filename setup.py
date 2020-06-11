import setuptools

setuptools.setup(
    name = 'condor',
    version = '0.1',
    author = 'Ayan Das',
    author_email = 'a.das@surrey.ac.uk',
    description = 'A software interface (python) to HTCondor job scheduler',
    packages = ['condor'],
    license = 'MIT License',
    keywords = 'HTCondor jobs scheduling HTC',
    install_requires = ['paramiko'],
    classifiers = [
        'Topic :: System :: Distributed Computing',
        'Topic :: Utilities',
        'Intended Audience :: Science/Research'
    ]
)
