#!/usr/bin/env python3

from distutils.core import setup

setup(name='Autorenamer',
      version='0.5',
      description='Rrename files to make them sort in given order.',
      author='Marcin Owsiany',
      author_email='marcin@owsiany.pl',
      url='http://marcin.owsiany.pl/autorenamer-page',
      packages=['autorenamer'],
      scripts=['autorenamer.py'],
      data_files = [
          ('share/applications', ['autorenamer.desktop']),
      ])
