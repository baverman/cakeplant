# -*- coding: utf-8 -*-
from datetime import datetime, date, timedelta

import pygtk
import gtk, gobject
pygtk.require("2.0") 

from taburet.accounts import AccountsPlan, Account
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
    
    def show_transactions_input_window(self, inout):
        date = self.get_date()
        transactions = self.bank_acc.transactions(date, date, income=inout, outcome=not inout).all()
        
        model = EditableListTreeModel(transactions,
            to_string=self.transaction_to_string(inout),
            on_row_change=self.save_transaction(inout),
            empty=self.new_transaction)
        
        init_editable_treeview(self.transactions_view, model,
            editable=('c_account', 'c_who', 'c_amount', 'c_what'),
            noneditable=('c_num',))
        
        self.transactions_window.show()

    def transaction_to_string(self, inout):
        def inner(row, cname):
            if cname == 'c_num':
                return getattr(row, 'num', 'None')
            elif cname == 'c_account':
                acc = row.from_acc if inout else row.to_acc
                if acc:
                    return Account.get(acc[-1]).name
                else:
                    return ''
            elif cname == 'c_who':
                return row.who
            elif cname == 'c_amount':
                return "%.2f" % row.amount
            elif cname == 'c_what':
                return row.what
            else:
                raise Exception("Unknown column %s" % cname)

        return inner
    
    def new_transaction(self):
        tran = Transaction()
        tran.what = ''
        tran.who = ''
        
        return tran 
    
    def save_transaction(self, inout):
        def inner(model, row, data):
            for k, v in data.items():
                if k == 'c_what':
                    row.what = v
                elif k == 'c_amount':
                    row.amount = float(v)
            row.save()
            
            self.update_saldo(self.get_date())
            
        return inner
