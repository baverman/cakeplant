# -*- coding: utf-8 -*-
from model import get_month_transaction_days, get_what_choice, get_who_choice, db as model_db

from ui.main import BankApp

class DbSetter(object):
    @staticmethod
    def set_db(db):
        model_db[0] = db

set_db = (DbSetter,)
same_db = 'taburet.transactions'
module_deps = ('taburet.accounts', )