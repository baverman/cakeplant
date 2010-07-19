from datetime import datetime, date, timedelta

import pygtk
import gtk, gobject
pygtk.require("2.0") 

import taburet.accounting
from .model import make_month_transaction_days_getter

from taburet.ui import process_focus_like_access, CommonApp, EditableListTreeModel, enable_edit_for_columns, process_edit_done, process_row_change

get_month_transaction_days = None

def set_db_for_models(db):
    global get_month_transaction_days
    get_month_transaction_days = make_month_transaction_days_getter(db)
    

class BankApp(CommonApp):
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
        model = EditableListTreeModel(transactions,
            (('num', '%d', gobject.TYPE_STRING), ('what', '%s', gobject.TYPE_STRING), ('amount', '%.2f', gobject.TYPE_STRING)),
            on_row_change=self.save_transaction,
            empty=self.new_transaction)
        enable_edit_for_columns(self.transactions_view, what=1, amount=2)
        self.transactions_view.set_model(model)
        self.transactions_window.show()
        
    def transactions_edit_done(self, renderer, path, new_text):
        process_edit_done(self.transactions_view, new_text)
        return process_focus_like_access(self.transactions_view)
    
    def transactions_cursor_changed(self, treeview):
        return process_row_change(treeview)
    
    def new_transaction(self):
        tran = taburet.accounting.Transaction()
        tran.num = -1
        tran.what = ''
        
        return tran 
    
    def save_transaction(self, model, row, data):
        for k, v in data.items():
            if k == 'what':
                row.what = v
            elif k == 'amount':
                row.amount = float(v)
        row.save()