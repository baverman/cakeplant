from setuptools import setup

setup(
    name     = 'cakeplant.apps.bank',
    version  = '0.1dev',
    author   = 'Anton Bobrov',
    author_email = 'bobrov@vl.ru',
    description = 'Bank and similar accounts filler',
    zip_safe   = False,
    packages = ['cakeplant.apps', 'cakeplant.apps.bank'],
    install_requires = ['cakeplant'],
    namespace_packages = ['cakeplant.apps'],
    entry_points = {
        'gui_scripts': [
            'cakeplant-bank = cakeplant.apps.bank:run',
        ]
    },
)
