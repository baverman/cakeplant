import sys
sys.path.append('./src')

import gtk

from taburet.utils import sync_design_documents
import taburet.accounting
import bank
import couchdbkit

s = couchdbkit.Server()
db = s.get_or_create_db('demo')
sync_design_documents(db, ('taburet.counter', 'taburet.accounting', 'bank'))
taburet.accounting.set_db_for_models(db)
bank.set_db_for_models(db)

bank.BankApp()
gtk.main()