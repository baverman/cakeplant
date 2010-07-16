from datetime import datetime, date, timedelta

import pygtk
import gtk, gobject
pygtk.require("2.0") 

import taburet.accounting

def debug(func):
    return func
    def inner(*args, **kwargs):
        print func.__name__, args, kwargs
        return func(*args, **kwargs)
    
    return inner

class TransactionListTreeModel(gtk.GenericTreeModel):
    def __init__(self, transactions):
        gtk.GenericTreeModel.__init__(self)
        self.transactions = transactions

    @debug
    def on_get_flags(self):
        return 0
    
    @debug
    def on_get_n_columns(self):
        return 3
    
    @debug
    def on_get_column_type(self, index):
        return gobject.TYPE_STRING
    
    @debug
    def on_get_path(self, node):
        return node
    
    @debug
    def on_get_iter(self, path):
        return path
    
    @debug
    def on_get_value(self, node, column):
        
        if not len(self.transactions):
            return None
        
        r = self.transactions[node[0]]
        
        if column == 0:
            return r.num
        elif column == 1:
            return r.what
        elif column == 2:
            return r.amount
        else:
            assert False, "Invalid column number %d" % column
    
    @debug
    def on_iter_next(self, node):
        if self.transactions:
            next = node[0] + 1
            if next < len(self.transactions):
                return (next,)
        
        return None

    @debug
    def on_iter_children(self, node):
        pass
    
    @debug
    def on_iter_has_child(self, node):
        return node == None
    
    @debug
    def on_iter_n_children(self, node):
        if node == None:
            return len(self.transactions)
        else:
            return 0
    
    @debug
    def on_iter_nth_child(self, node, n):
        if node == None:
            return (n,)
        else:
            return None
    
    @debug
    def on_iter_parent(self, node):
        return None

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
        self.transactions_window = builder.get_object('TransactionInput')
        self.transactions_view = builder.get_object('transactions')
        
        self.plan = taburet.accounting.AccountsPlan()
        self.bank_acc = self.plan.get_by_name('51/1')
        
        self.date_changed(date.today())
        self.set_date(date.today())
    
    def show_dialog(self, widget, data=None):
        pass
    
    def gtk_main_quit(self, widget):
        gtk.main_quit()

    def on_date_day_selected(self, widget, data=None):
        self.date_changed(self.get_date())
        
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
    
    def get_date(self):
        return datetime(self.date.props.year, self.date.props.month + 1, self.date.props.day)
    
    def on_outcome_transactions_clicked(self, widget):
        date = self.get_date()
        self.show_transactions_input_window(self.bank_acc.transactions(date, date, outcome=True).all())
    
    def on_income_transactions_clicked(self, widget):
        date = self.get_date()
        self.show_transactions_input_window(self.bank_acc.transactions(date, date, income=True).all())
    
    def show_transactions_input_window(self, transactions):
        model = TransactionListTreeModel(transactions)
        
        if not self.transactions_view.get_model():
            cell = gtk.CellRendererText()
            column = gtk.TreeViewColumn("num", cell, text=0)
            self.transactions_view.append_column(column)
            
            column = gtk.TreeViewColumn("what", cell, text=1)
            self.transactions_view.append_column(column)
            
            column = gtk.TreeViewColumn("how", cell, text=2)
            self.transactions_view.append_column(column)
            
        self.transactions_view.set_model(model)
        
        self.transactions_window.show()
        
    def gtk_widget_hide(self, widget, data=None):
        widget.hide()
        return True
