import sys
sys.path.append('./src')

import gtk

from taburet.utils import sync_design_documents
import taburet.accounting

import couchdbkit

from bank import BankApp

s = couchdbkit.Server()
db = s.get_or_create_db('demo')
sync_design_documents(db, ('taburet.counter', 'taburet.accounting'))
taburet.accounting.set_db_for_models(db)

BankApp()
gtk.main()