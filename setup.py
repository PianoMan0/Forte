from cx_Freeze import setup, Executable
import sys

# Ensure the `encodings` package is available at runtime and not packed
# inside the zip archive where the runtime bootstrap may not find it.
build_exe_options = {
      "packages": ["encodings"],
      "include_files": [],
      # Keep encodings out of the zip so Python's bootstrap can import it.
      "zip_include_packages": ["*"],
      "zip_exclude_packages": ["encodings"],
      "include_msvcr": True,
}

base = None
if sys.platform == "win32":
      base = None

executables = [Executable('main.py', base=base)]

setup(
      name='Forte',
      version='1.0',
      description='A voice assistant built with Python',
      options={"build_exe": build_exe_options},
      executables=executables,
)