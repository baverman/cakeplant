from setuptools import setup, find_packages

setup(
    name     = 'cakeplant.apps.exp',
    version  = '0.1dev',
    author   = 'Anton Bobrov',
    author_email = 'bobrov@vl.ru',
    description = 'Expedition work place',
    zip_safe   = False,
    packages = find_packages(),
    install_requires = ['cakeplant'],
    namespace_packages = ['cakeplant', 'cakeplant.apps'],
    entry_points = {
        'gui_scripts': [
            'cakeplant-exp = cakeplant.apps.exp:run',
        ]
    },
)
