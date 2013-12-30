from setuptools import setup, find_packages

setup(
    name='gpdiff',
    description='Compute 2-way and 3-way diffs of GuitarPro tablatures',
    version='0.1',
    author='Sviatoslav Abakumov',
    author_email='dust.harvesting@gmail.com',
    url='https://bitbucket.org/Perlence/gpdiff/',
    platforms=['Windows', 'POSIX', 'Unix', 'MacOS X'],
    license='zlib/libpng',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'PyGuitarPro',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: zlib/libpng License',
        'Natural Language :: English',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Artistic Software',
        'Topic :: Multimedia :: Sound/Audio',
    ],
)
