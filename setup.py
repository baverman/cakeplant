from setuptools import setup, find_packages

setup(
    name     = 'cakeplant',
    version  = '0.1dev',
    author   = 'Anton Bobrov',
    author_email = 'bobrov@vl.ru',
    description = 'Accounting for bakeries',
#    long_description = open('README.rst').read(),
    zip_safe   = False,
    packages = find_packages(),
    install_requires = ['taburet'],
    include_package_data = True,
    #entry_points = {
    #    'gui_scripts': [
    #        'snaked = snaked.core.run:run',
    #    ]
    #},
    url = 'http://github.com/baverman/cakeplant',
    classifiers = [
        "Programming Language :: Python",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: Developers",
        "Natural Language :: Russian",
    ],
)
