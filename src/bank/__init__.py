from datetime import datetime, date, timedelta

import pygtk
import gtk, gobject
pygtk.require("2.0") 

import taburet.accounting
from .model import make_month_transaction_days_getter

def debug(func):
    return func
    def inner(*args):
        print func.__name__, args[1:]
        return func(*args)
    
    return inner

get_month_transaction_days = None

def set_db_for_models(db):
    global get_month_transaction_days
    get_month_transaction_days = make_month_transaction_days_getter(db)
    

class TransactionListTreeModel(gtk.GenericTreeModel):
    def __init__(self, transactions):
        gtk.GenericTreeModel.__init__(self)
        self.transactions = transactions

    @debug
    def on_get_flags(self):
        return gtk.TREE_MODEL_LIST_ONLY
    
    @debug
    def on_get_n_columns(self):
        return 3
    
    @debug
    def on_get_column_type(self, index):
        return (gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_BOOLEAN)[index]
    
    @debug
    def on_get_path(self, node):
        return node
    
    @debug
    def on_get_iter(self, path):
        return path if self.transactions else None 
    
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
            return "%.2f" % r.amount
        elif column == 3:
            return True
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
        
        self.update_saldo(date.today())
        self.on_date_month_changed(self.date)
        self.set_date(date.today())
    
    def show_dialog(self, widget, data=None):
        pass
    
    def gtk_main_quit(self, widget):
        gtk.main_quit()

    def on_date_day_selected(self, widget, data=None):
        self.update_saldo(self.get_date())
        
    def update_saldo(self, date):
        balance = self.bank_acc.balance(date, date)
        
        self.in_total.props.label = "%.2f" % balance.debet
        self.out_total.props.label = "%.2f" % balance.kredit
        
        saldo = self.bank_acc.balance(None, date - timedelta(days=1))
        
        self.begin_saldo.props.label = "%.2f" % saldo.balance
        self.end_saldo.props.label = "%.2f" % (saldo.balance + balance.balance)
        
    def on_date_month_changed(self, widget):
        date = self.get_date()
        self.date.clear_marks()
        map(self.date.mark_day, get_month_transaction_days(self.bank_acc, date.year, date.month))
    
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
        self.transactions_view.set_model(model)
        self.transactions_window.show()
        
    def gtk_widget_hide(self, widget, data=None):
        widget.hide()
        return True
    
    def editing_started(self, renderer, editable, path, data=None):
        editable.connect('key-press-event', self.check_and_change_editable, renderer)
        
    def edit_done(self, renderer, path, new_text):
        current_column = self.transactions_view.get_cursor()[1]
        columns = self.transactions_view.get_columns()
        for i, c in enumerate(columns):
            if c == current_column:
                break
            
        if i >= len(columns):
            return
        
        while True:
            i += 1
            if i >= len(columns):
                model = self.transactions_view.get_model()
                next_iter = model.iter_next(model.get_iter_from_string(path))
                if not next_iter:
                    break
                
                path = model.get_string_from_iter(next_iter)
                i = -1
                continue
            
            next_column = columns[i]
            if next_column.get_cell_renderers()[0].props.editable:
                self.transactions_view.set_cursor(path, next_column, True)
                break