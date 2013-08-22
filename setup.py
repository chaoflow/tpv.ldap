from setuptools import setup, find_packages
import sys, os

version = '0.8.dev0'
shortdesc = 'Connect the vortex to ldap'
#longdesc = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

install_requires = [
    'setuptools',
    'tpv',
    'pyldap',
]


if sys.version_info < (2, 7):
    install_requires.append('unittest2')
    install_requires.append('ordereddict')


setup(name='tpv.ldap',
      version=version,
      description=shortdesc,
      #long_description=longdesc,
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development',
        ],
      keywords='',
      author='Florian Friesdorf',
      author_email='flo@chaoflow.net',
      url='http://github.com/chaoflow/tpv.ldap',
      license='AGPLv3+',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages=['tpv'],
      include_package_data=True,
      zip_safe=True,
      install_requires=install_requires,
      )
