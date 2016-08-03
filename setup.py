import os
from distutils.core import setup

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(
    name="djmp",
    version="0.2",
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
    zip_safe=False,
    install_requires=[
        'Django==1.8.7',
        'MapProxy==1.9.0',
        'PyYAML>=3.10',
        'django-tastypie>=0.12.1',
        'Shapely>=1.5.9',
        'psutil>=3.0.1',
        'pyproj==1.9.5.1',
    ]
)
