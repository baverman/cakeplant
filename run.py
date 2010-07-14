from datetime import datetime, date
import pygtk
import gtk
pygtk.require("2.0") 

from taburet.utils import sync_design_documents
import taburet.accounting

import couchdbkit

s = couchdbkit.Server()
db = s.get_or_create_db('demo')
sync_design_documents(db, ('taburet.counter', 'taburet.accounting'))
taburet.accounting.set_db_for_models(db)


class BankApp(object):
    def __init__(self):
        builder = gtk.Builder()
        builder.add_from_file("src/bank/glade/main.glade")
        builder.connect_signals(self)
        self.window = builder.get_object("Bank")
        self.window.show()
        
        self.in_total = builder.get_object('in_total')
        self.out_total = builder.get_object('out_total')
        
        self.plan = taburet.accounting.AccountsPlan()
        
        self.bank_acc = self.plan.get_by_name('51/1')
        
        self.date_changed(date.today())
    
    def show_dialog(self, widget, data=None):
        pass
    
    def gtk_main_quit(self, widget):
        gtk.main_quit()

    def on_date_day_selected(self, widget, data=None):
        self.date_changed(datetime(widget.props.year, widget.props.month, widget.props.day))
        
    def date_changed(self, date):
        balance = self.bank_acc.balance(date, date)
        
        self.in_total.props.label = "%.2f" % balance.debet
        self.out_total.props.label = "%.2f" % balance.kredit

BankApp()
gtk.main()