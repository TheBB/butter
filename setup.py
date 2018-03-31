#!/usr/bin/env python3

from distutils.core import setup

setup(
    name='Butter',
    version='0.1',
    description='Image database',
    author='Eivind Fonn',
    author_email='evfonn@gmail.com',
    license='GPL3',
    url='https://github.com/TheBB/butter',
    py_modules=['butter'],
    entry_points={
        'console_scripts': ['butter=butter.__main__:main'],
    },
    install_requires=[
        'click',
        'imagehash',
        'inflect',
        'pillow',
        'pyqt5',
        'pyxdg',
        'requests',
        'sqlalchemy',
        'selenium',
        'tqdm',
        'yapsy',
    ],
)
