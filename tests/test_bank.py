# -*- coding: utf-8 -*-
import sys, os.path
import py.test #@UnresolvedImport

from couchdbkit import Server, MultipleResultsFound

from datetime import datetime

SRC_PATH = os.path.abspath(os.path.join(os.path.split(__file__)[0], '..', 'src'))
sys.path.insert(0, SRC_PATH)

from taburet.utils import sync_design_documents
from taburet.accounting import AccountsPlan
import bank
import taburet.accounting

TEST_DB = 'test'

def pytest_funcarg__db(request):
    s = Server()
    
    if TEST_DB in s:
        del s[TEST_DB]
    
    db = s.create_db(TEST_DB)

    taburet.accounting.set_db_for_models(db)
    bank.set_db_for_models(db)
    
    sync_design_documents(db, ('taburet.counter', 'taburet.accounting', 'bank'))
    
    return db

def test_transaction_days(db):
    plan = AccountsPlan()
    
    acc1 = plan.add_account()
    acc2 = plan.add_account()
    
    plan.create_transaction(acc1, acc2, 200.0, datetime(2010, 5, 20)).save()
    plan.create_transaction(acc1, acc2, 300.0, datetime(2010, 5, 31)).save()
    plan.create_transaction(acc1, acc2, 100.0, datetime(2010, 6, 01)).save()
    
    result = bank.get_month_transaction_days(acc1, 2010, 5)
    assert result == [20, 31]
    
    result = bank.get_month_transaction_days(acc2, 2010, 6)
    assert result == [1]
    
    result = bank.get_month_transaction_days(acc2, 2010, 7)
    assert result == []    