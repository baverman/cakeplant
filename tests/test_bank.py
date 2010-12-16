# -*- coding: utf-8 -*-
from datetime import datetime

from taburet import PackageManager
from taburet.test import TestServer

from taburet.accounts import AccountsPlan

from cakeplant import bank

def pytest_funcarg__db(request):
    s = TestServer()

    db = s.get_db('test')
    pm = PackageManager()
    pm.use('cakeplant.bank')
    pm.set_db(db, 'taburet.transactions', 'taburet.accounts')
    pm.sync_design_documents()

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

def test_what_choice(db):
    plan = AccountsPlan()

    acc1 = plan.add_account()
    acc2 = plan.add_account()

    t = plan.create_transaction(acc1, acc2, 200.0)
    t.what = u'за хлеб'
    t.save()

    t = plan.create_transaction(acc1, acc2, 300.0)
    t.what = u'за воду'
    t.save()

    result = bank.get_what_choice()
    assert result == [u'за воду', u'за хлеб']

    t = plan.create_transaction(acc1, acc2, 300.0)
    t.what = u'за воду'
    t.save()

    result = bank.get_what_choice()
    assert result == [u'за воду', u'за хлеб']

def test_who_choice(db):
    plan = AccountsPlan()

    acc1 = plan.add_account()
    acc2 = plan.add_account()

    t = plan.create_transaction(acc1, acc2, 200.0)
    t.who = u'Бичиков'
    t.save()

    t = plan.create_transaction(acc1, acc2, 300.0)
    t.who = u'Зубков'
    t.save()

    result = bank.get_who_choice()
    assert result == [u'Бичиков', u'Зубков']

    t = plan.create_transaction(acc1, acc2, 300.0)
    t.who = u'Зубков'
    t.save()

    result = bank.get_who_choice()
    assert result == [u'Бичиков', u'Зубков']