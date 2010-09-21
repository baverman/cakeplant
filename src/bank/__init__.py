# -*- coding: utf-8 -*-
from datetime import datetime, date, timedelta

import pygtk
import gtk, gobject
pygtk.require("2.0") 

from taburet.accounts import AccountsPlan, Account, accounts_walk 
from taburet.transactions import Transaction
from model import make_month_transaction_days_getter

from taburet.ui import process_focus_like_access, CommonApp, EditableListTreeModel, init_editable_treeview

get_month_transaction_days = None

class DbSetter(object):
    @staticmethod
    def set_db(db):
        global get_month_transaction_days
        get_month_transaction_days = make_month_transaction_days_getter(db)
    

set_db = (DbSetter,)
same_db = 'taburet.transactions'
module_deps = ('taburet.accounts', )

class DocColumn(object):
    def __init__(self, attr, editable=True):
        self.attr = attr
        self.editable = editable
        
    def to_string(self, row):
        return self.value_to_string(getattr(row, self.attr, None))
    
    def get_properties(self):
        return {'editable': self.editable}


class TextDocColumn(DocColumn):
    def from_string(self, value):
        return value
    
    def value_to_string(self, value):
        return value


class AccountColumn(DocColumn):
    def __init__(self, attr, choices, editable=True):
        DocColumn.__init__(self, attr, editable)
        self.choices = choices

        model = gtk.ListStore(str)
        
        for k, v in self.choices:
            model.append((v,))
            
        self.completion = gtk.EntryCompletion()
        self.completion.set_model(model)
        self.completion.set_text_column(0)
        self.completion.set_inline_completion(True)
        self.completion.set_inline_selection(True)

    def from_string(self, value):
        return value
    
    def value_to_string(self, value):
        if not value:
            return ''
    
        for k, v in self.choices:
            if k == value[-1]:
                return v
    
        return 'Undef'

    def on_editing_started(self, renderer, editable, path):    
        editable.set_completion(self.completion)
        return False        
        

class IntegerDocColumn(DocColumn):
    def from_string(self, value):
        return int(value)
    
    def value_to_string(self, value):
        return str(value)


class FloatDocColumn(DocColumn):
    def __init__(self, attr, format='%.2f', editable=True):
        DocColumn.__init__(self, attr, editable)
        self.format = format
        
    def from_string(self, value):
        return float(value)
    
    def value_to_string(self, value):
        return self.format % value

class TransactionModel(object):
    def __init__(self, inout):
        self.inout = inout

        choices = [(r._id, r.name) for _, r in accounts_walk(AccountsPlan().accounts(), True)]

        self.c_num = IntegerDocColumn('num', editable=False)
        self.c_account = AccountColumn('from_acc' if inout else 'to_acc', choices)
        self.c_who = TextDocColumn('who')
        self.c_amount = FloatDocColumn('amount')
        self.c_what = TextDocColumn('what')

    def new(self):
        tran = Transaction()
        tran.what = ''
        tran.who = ''
        
        return tran 

    def row_changed(self, model, row, data):
        if data:
            if 'c_what' in data:
                row.what = data['c_what']
            if 'c_amount' in data:
                row.amount = data['c_amount']
            row.save()
    

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
        
        self.plan = AccountsPlan()
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
        self.show_transactions_input_window(False)
    
    def on_income_transactions_clicked(self, widget):
        self.show_transactions_input_window(True)

    def on_transaction_input_hide(self, *args):    
        self.update_saldo(self.get_date())
        
    def show_transactions_input_window(self, inout):
        date = self.get_date()
        transactions = self.bank_acc.transactions(date, date, income=inout, outcome=not inout).all()
        
        model = EditableListTreeModel(transactions, TransactionModel(inout))
        init_editable_treeview(self.transactions_view, model)
        
        self.transactions_window.show()
