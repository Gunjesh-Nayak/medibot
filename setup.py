try:
    # Prefer setuptools when available
    from setuptools import setup, find_packages  # type: ignore
    _use_setuptools = True
except Exception:
    # Fallback to distutils.core when setuptools is not installed or importable
    from distutils.core import setup  # type: ignore
    import os

    def find_packages():
        """A minimal find_packages implementation to locate packages with __init__.py."""
        packages = []
        for dirpath, dirnames, filenames in os.walk('.'):
            if '__init__.py' in filenames:
                pkg = os.path.relpath(dirpath, '.').replace(os.sep, '.')
                if pkg in ('.', ''):
                    continue
                packages.append(pkg.lstrip('.'))
        return packages

    _use_setuptools = False

# Common metadata
kwargs = dict(
    name='HealthAIChatBot',
    version='1.0.0',
    author='Gunjesh Nayak',
    author_email='abc.onlinehost@gmail.com',
    packages=find_packages(),
)

# Only include setuptools-specific options when setuptools is available
if _use_setuptools:
    kwargs['install_requires'] = []

setup(**kwargs)



