#!/usr/bin/env python

import sys
sys.path.append('./src')

from datetime import date

import bank.reports.kassa
import bank.reports.month

from taburet import PackageManager
from taburet.accounts import AccountsPlan
import couchdbkit

import taburet.report.excel

s = couchdbkit.Server()
db = s.get_or_create_db('demo')

pm = PackageManager()
pm.use('bank')
pm.set_db(db, 'taburet.transactions', 'taburet.accounts')
pm.sync_design_documents()

plan = AccountsPlan()
account = plan.get_by_name('51/1')

report = bank.reports.kassa.do(account, date(2010, 5, 4))
#report = bank.reports.month.do(account, date(2010, 4, 4), True)
taburet.report.excel.save(report, '/tmp/wow.xls')
