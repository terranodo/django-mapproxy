import os
from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

# Tell distutils not to put the data_files in platform-specific installation
# locations. See here for an explanation:
# http://groups.google.com/group/comp.lang.python/browse_thread/thread/35ec7b2fed36eaec/2105ee4d9e8042cb
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)
geonode_dir = 'geonode'

for dirpath, dirnames, filenames in os.walk(geonode_dir):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'):
            del dirnames[i]
    if '__init__.py' in filenames:
        packages.append('.'.join(fullsplit(dirpath)))
    elif filenames:
        data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

setup(
    name="djmp",
    version="0.1",
    author="",
    author_email="",
    description="django-mapproxy adaptor",
    long_description=(read('README.md')),
    # Full list of classifiers can be found at:
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 1 - Planning',
    ],
    license="BSD",
    keywords="django mapproxy",
    url='https://github.com/terranodo/django-mapproxy',
    packages=['djmp',],
    include_package_data=True,
    data_files=data_files,
    zip_safe=False,
    install_requires=[
        'Django==1.11.23',
        'MapProxy==1.9.0',
        'PyYAML>=3.10',
        'django-tastypie==0.13.3',
        'psutil>=3.0.1',
        'pyproj==1.9.5.1',
        'webtest==2.0.20',
        'django-guardian==1.4.4',
        'python-dateutil==2.5.3',
        'mimeparse==0.1.3',
        'WebOb==1.6.1',
    ]
)
