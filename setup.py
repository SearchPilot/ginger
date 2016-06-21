from setuptools import setup, find_packages

setup(name='ginger',
      version="0.0.4",
      packages=find_packages(),
      description='A very lightweight static site generator',
      url='https://github.com/DistilledLtd/ginger',
      author='Distilled Ltd',
      author_email='randd@distilled.net',
      install_requires=['csscompressor', 'Jinja2', 'jsmin', 'libsass', 'PyYAML', 'watchdog', ],
      entry_points={
          'console_scripts': [
              'ginger = ginger.__main__:ginger',
          ]
      },
      )
