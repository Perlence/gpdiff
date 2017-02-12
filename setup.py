from setuptools import setup, find_packages

setup(
    name='gpdiff',
    description='Compute 2-way and 3-way diffs of GuitarPro tablatures',
    version='0.1',
    author='Sviatoslav Abakumov',
    author_email='dust.harvesting@gmail.com',
    url='https://bitbucket.org/Perlence/gpdiff/',
    platforms=['Windows', 'POSIX', 'Unix', 'MacOS X'],
    license='GPL',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'gpdiff = gpdiff.gpdiff:main',
        ],
    },
    install_requires=[
        'attrs',
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
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Artistic Software',
        'Topic :: Multimedia :: Sound/Audio',
    ],
)
