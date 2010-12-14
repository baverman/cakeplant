# -*- coding: utf-8 -*-
from datetime import datetime, date, timedelta

import gtk

from taburet.accounts import AccountsPlan, accounts_walk
from taburet.transactions import Transaction
from model import make_month_transaction_days_getter
from taburet.ui.feedback import show_message

from taburet.ui import CommonApp, BuilderAware, idle, join_to_file_dir
from taburet.ui.grid import (Grid, GridColumn, BadValueException,
    IntGridColumn, FloatGridColumn, DirtyRow)

get_month_transaction_days = None

class DbSetter(object):
    @staticmethod
    def set_db(db):
        global get_month_transaction_days
        get_month_transaction_days = make_month_transaction_days_getter(db)


set_db = (DbSetter,)
same_db = 'taburet.transactions'
module_deps = ('taburet.accounts', )

class AccountColumn(GridColumn):
    def __init__(self, attr, choices, *args, **kwargs):
        GridColumn.__init__(self, attr, *args, **kwargs)
        self.choices = choices
        self.model = gtk.ListStore(str)

        for k, v in self.choices:
            self.model.append((v,))

    def update_row_value(self, dirty_row, row):
        value = dirty_row[self.name]
        acc = AccountsPlan().get_by_name(value)
        if not acc:
            raise BadValueException('Счет не найден. Введите правильный номер счета')

        row[self.name] = acc.account_path

    def _set_value(self, entry, row):
        value = row[self.name]
        if not value:
            return entry.set_text('')

        for k, v in self.choices:
            if k == value[-1]:
                entry.set_text(v)
                return

        entry.set_text('Undef')

    def create_widget(self, *args):
        w = super(AccountColumn, self).create_widget(*args)

        completion = gtk.EntryCompletion()
        completion.set_model(self.model)
        completion.set_text_column(0)
        completion.set_inline_completion(True)
        completion.set_inline_selection(True)

        w.set_completion(completion)

        return w


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

    def create_transactions_view(self, inout):
        choices = [(r._id, r.name) for _, r in accounts_walk(AccountsPlan().accounts(), True)]

        columns = [
            IntGridColumn('num', '№', editable=False, width=3),
            AccountColumn('from_acc' if inout else 'to_acc', choices, 'Счет', width=4),
            GridColumn('who', 'Контрагент', width=15),
            FloatGridColumn('amount', 'Сколько', width=7),
            GridColumn('what', 'За что', width=10),
        ]

        return Grid(columns)

    def show_transactions_input_window(self, inout):
        date = self.get_date()
        transactions = sorted(self.bank_acc.transactions(
            date, date, income=inout, outcome=not inout), key=lambda r: r.num)

        last = self.last_in_num_param if inout else self.last_out_num_param

        w = [self.sw.get_child()]
        if w[0]:
            self.sw.remove(w[0])
            w[0].destroy()
        w[:] = []


        dt = self.get_date()

        def new():
            tran = Transaction()
            tran.what = ''
            tran.who = ''
            tran.date = dt

            tran._isnew_ = True

            if inout:
                tran.to_acc = self.bank_acc.account_path
            else:
                tran.from_acc = self.bank_acc.account_path

            return tran

        def on_commit(dr, row):
            if not hasattr(row, 'num'):
                row.num = last.inc()

            row.save()

            if hasattr(row, '_isnew_'):
                del row._isnew_
                transactions.append(new())
                dr.jump_to_new_row(1)

        def on_error(dr, e):
            show_message(self.sw, str(e), 5000)

        tv = self.create_transactions_view(inout)
        self.sw.add(tv)

        transactions.append(new())
        tv.set_model(transactions, DirtyRow(tv, on_commit, on_error))
        tv.show_all()

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
