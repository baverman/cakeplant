#!/usr/bin/env python

import gtk
import couchdbkit

from taburet import PackageManager, config
import cakeplant.bank

s = couchdbkit.Server()
db = s.get_or_create_db('demo')

conf = config.Configuration(s.get_or_create_db('demo_config'))

pm = PackageManager()
pm.use('cakeplant.bank')
pm.set_db(db, 'taburet.transactions', 'taburet.accounts')
pm.sync_design_documents()

cakeplant.bank.BankApp(conf)
gtk.main()
