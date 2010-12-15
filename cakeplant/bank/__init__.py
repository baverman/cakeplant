# -*- coding: utf-8 -*-
from model import get_month_transaction_days

from ui.main import BankApp

class DbSetter(object):
    @staticmethod
    def set_db(db):
        get_month_transaction_days.db = db

set_db = (DbSetter,)
same_db = 'taburet.transactions'
module_deps = ('taburet.accounts', )