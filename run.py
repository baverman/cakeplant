#!/usr/bin/env python

import sys
sys.path.append('./src')

import gtk
import couchdbkit

from taburet import PackageManager 
import bank

s = couchdbkit.Server()
db = s.get_or_create_db('demo')

pm = PackageManager()
pm.use('bank')
pm.set_db(db, 'taburet.transactions', 'taburet.accounts')
pm.sync_design_documents()

bank.BankApp()
gtk.main()
