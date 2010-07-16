from datetime import datetime, date, timedelta

import pygtk
import gtk
pygtk.require("2.0") 

import taburet.accounting

class BankApp(object):
    def __init__(self):
        builder = gtk.Builder()
        builder.add_from_file("src/bank/glade/main.glade")
        builder.connect_signals(self)
        self.window = builder.get_object("Bank")
        self.window.show()

        # getting widgets
        self.in_total = builder.get_object('in_total')
        self.out_total = builder.get_object('out_total')
        self.begin_saldo = builder.get_object('begin_saldo')
        self.end_saldo = builder.get_object('end_saldo')
        self.date = builder.get_object('date')
        
        self.plan = taburet.accounting.AccountsPlan()
        self.bank_acc = self.plan.get_by_name('51/1')
        
        self.date_changed(date.today())
        self.set_date(date.today())
    
    def show_dialog(self, widget, data=None):
        pass
    
    def gtk_main_quit(self, widget):
        gtk.main_quit()

    def on_date_day_selected(self, widget, data=None):
        self.date_changed(datetime(widget.props.year, widget.props.month + 1, widget.props.day))
        
    def date_changed(self, date):
        balance = self.bank_acc.balance(date, date)
        
        self.in_total.props.label = "%.2f" % balance.debet
        self.out_total.props.label = "%.2f" % balance.kredit
        
        saldo = self.bank_acc.balance(None, date - timedelta(days=1))
        
        self.begin_saldo.props.label = "%.2f" % saldo.balance
        self.end_saldo.props.label = "%.2f" % (saldo.balance + balance.balance)
    
    def set_date(self, date):
        self.date.props.year = date.year
        self.date.props.month = date.month - 1
        self.date.props.day = date.day