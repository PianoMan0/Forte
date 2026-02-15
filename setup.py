from cx_Freeze import setup, Executable

executables = [Executable('main.py')]

setup(name='Forte',
      version='1.0',
      description='A voice assistant built with Python',
      executables=executables)