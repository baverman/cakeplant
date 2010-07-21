#!/usr/bin/env python

import sys
sys.path.append('./src')

from datetime import date

import bank.reports.kassa
import bank.reports.month

from taburet.utils import sync_design_documents
import taburet.accounting
import bank
import couchdbkit

s = couchdbkit.Server()
db = s.get_or_create_db('demo')
#sync_design_documents(db, ('taburet.counter', 'taburet.accounting', 'bank'))
taburet.accounting.set_db_for_models(db)
bank.set_db_for_models(db)

plan = taburet.accounting.AccountsPlan()
account = plan.get_by_name('51/1')

#bank.reports.kassa.do(account, date(2010, 5, 4), '/tmp/wow.xls')
bank.reports.month.do(account, date(2010, 4, 4), False, '/tmp/wow.xls') 