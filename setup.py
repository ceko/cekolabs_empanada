from distutils.core import setup


setup(
    name='cekolabs_empanada',
    version='0.1.1',
    author='Dave Lafferty',
    author_email='info@dave-lafferty.com',
    packages=['cekolabs_empanada',],
    scripts=[],
    url='https://github.com/ceko/cekolabs_empanada', #TODO: Switch to github
    license='LICENSE.txt',
    description='All the django widgets used on www.dave-lafferty.com.',
    long_description=open('README.txt').read(),
    install_requires=[],
)