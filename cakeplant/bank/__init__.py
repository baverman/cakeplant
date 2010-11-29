# -*- coding: utf-8 -*-
from datetime import datetime, date, timedelta

import gtk

from taburet.accounts import AccountsPlan, accounts_walk
from taburet.transactions import Transaction
from model import make_month_transaction_days_getter

from taburet.ui import CommonApp, BuilderAware, idle, join_to_file_dir
from taburet.ui.model import EditableListTreeModel
from taburet.ui.tree import init_editable_treeview

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

    def from_string(self, row, value):
        setattr(row, self.attr, self.string_to_value(value))

    def string_to_value(self, value):
        return value

    def value_to_string(self, value):
        return value

    def get_value(self, row, default=None):
        return getattr(row, self.attr, default)

    def get_properties(self):
        return {'editable': self.editable}


class TextDocColumn(DocColumn):
    pass

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

    def string_to_value(self, value):
        acc = AccountsPlan().get_by_name(value)
        if not acc:
            raise ValueError(u'Счет не найден. Введите правильный номер счета')

        return acc.account_path

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
    def string_to_value(self, value):
        return int(value)

    def value_to_string(self, value):
        return str(value)


class FloatDocColumn(DocColumn):
    def __init__(self, attr, format='%.2f', editable=True):
        DocColumn.__init__(self, attr, editable)
        self.format = format

    def string_to_value(self, value):
        return float(value)

    def value_to_string(self, value):
        return self.format % value

class TransactionModel(object):
    def __init__(self, last, inout, other_account, dt):
        self.inout = inout
        self.other_account = other_account
        self.dt = dt
        self.last = last

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
        tran.date = self.dt

        if self.inout:
            tran.to_acc = self.other_account
        else:
            tran.from_acc = self.other_account

        return tran

    def row_changed(self, model, row):
        if not hasattr(row, 'num'):
            row.num = self.last.inc()

        row.save()

class BankApp(CommonApp, BuilderAware):
    def __init__(self, conf):
        self.conf = conf

        BuilderAware.__init__(self, join_to_file_dir(__file__, "glade", "main.glade"))

        self.plan = AccountsPlan()
        self.bank_acc = self.plan.get_by_name('51/1')

        self.last_in_num_param = self.conf.param('last_in_num_for_'+self.bank_acc._id)
        self.last_out_num_param = self.conf.param('last_out_num_for_'+self.bank_acc._id)

        self.update_saldo(date.today())
        self.on_date_month_changed(self.date)
        self.set_date(date.today())
        self.update_last_nums()

        self.window.show()

    def on_date_day_selected(self, widget, data=None):
        self.update_saldo(self.get_date())

    def update_saldo(self, date):
        balance = self.bank_acc.balance(date, date)

        self.in_total.props.label = "%.2f" % balance.debet
        self.out_total.props.label = "%.2f" % balance.kredit

        saldo = self.bank_acc.balance(None, date - timedelta(days=1))

        self.begin_saldo.props.label = "%.2f" % saldo.balance
        self.end_saldo.props.label = "%.2f" % (saldo.balance + balance.balance)

    def update_last_nums(self):
        self.last_in_num.set_text(str(self.last_in_num_param.get(0)))
        self.last_out_num.set_text(str(self.last_out_num_param.get(0)))

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
        idle(self.update_saldo, self.get_date())
        idle(self.update_last_nums)

    def show_transactions_input_window(self, inout):
        date = self.get_date()
        transactions = sorted(self.bank_acc.transactions(
            date, date, income=inout, outcome=not inout), key=lambda r: r.num)

        last = self.last_in_num_param if inout else self.last_out_num_param

        model = EditableListTreeModel(transactions,
            TransactionModel(last, inout, self.bank_acc.account_path, self.get_date()))

        init_editable_treeview(self.transactions_view, model)

        self.transactions_window.show()

    def on_last_out_num_focus_out_event(self, entry, event):
        self.last_out_num_param.set(int(entry.get_text()))

    def on_last_in_num_focus_out_event(self, entry, event):
        self.last_in_num_param.set(int(entry.get_text()))

    def on_kassa_report_activate(self, *args):
        import reports.kassa
        import taburet.report.excel
        import tempfile
        import subprocess

        report = reports.kassa.do(self.bank_acc, self.get_date())
        filename = tempfile.mkstemp('.xls')[1]
        taburet.report.excel.save(report, filename)

        subprocess.Popen(['/usr/bin/env', 'xdg-open', filename]).poll()

    def on_in_report_activate(self, *args):
        import reports.month
        import taburet.report.excel
        import tempfile
        import subprocess

        report = reports.month.do(self.bank_acc, self.get_date(), True)
        filename = tempfile.mkstemp('.xls')[1]
        taburet.report.excel.save(report, filename)

        subprocess.Popen(['/usr/bin/env', 'xdg-open', filename]).poll()

    def on_out_report_activate(self, *args):
        import reports.month
        import taburet.report.excel
        import tempfile
        import subprocess

        report = reports.month.do(self.bank_acc, self.get_date(), False)
        filename = tempfile.mkstemp('.xls')[1]
        taburet.report.excel.save(report, filename)

        subprocess.Popen(['/usr/bin/env', 'xdg-open', filename]).poll()
