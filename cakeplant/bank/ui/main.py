# -*- coding: utf-8 -*-
from datetime import datetime, date, timedelta

from taburet.ui import CommonApp, BuilderAware, idle, join_to_file_dir
from taburet.accounts import AccountsPlan

from ..model import get_month_transaction_days

class BankApp(CommonApp, BuilderAware):
    """glade-file: main.glade"""
    def __init__(self, conf, account_name):
        self.conf = conf

        BuilderAware.__init__(self, join_to_file_dir(__file__, "main.glade"))

        self.plan = AccountsPlan()
        self.bank_acc = self.plan.get_by_name(account_name)

        self.last_in_num_param = self.conf.param('last_in_num_for_'+self.bank_acc._id)
        self.last_out_num_param = self.conf.param('last_out_num_for_'+self.bank_acc._id)

        self.update_saldo(date.today())
        self.on_date_month_changed(self.date)
        self.set_date(date.today())
        self.update_last_nums()

        self.window.set_title(
            conf.get('firm_name', 'WTF?') + ' | ' + self.bank_acc.name + ' ' + self.bank_acc.desc)

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

    def show_transactions_input_window(self, inout):
        from transactions import TransactionsForm
        form = TransactionsForm(inout, self.bank_acc, self.get_date(),
            self.last_in_num_param, self.last_out_num_param, self.on_transaction_input_hide)
        form.show()

    def on_transaction_input_hide(self, *args):
        idle(self.update_saldo, self.get_date())
        idle(self.update_last_nums)

    def on_last_out_num_focus_out_event(self, entry, event):
        self.last_out_num_param.set(int(entry.get_text()))

    def on_last_in_num_focus_out_event(self, entry, event):
        self.last_in_num_param.set(int(entry.get_text()))

    def on_kassa_report_activate(self, *args):
        from ..reports import kassa
        import taburet.report.excel
        import tempfile
        from taburet.utils import start_file

        report = kassa.do(self.bank_acc, self.get_date())
        filename = tempfile.mkstemp('.xls')[1]
        taburet.report.excel.save(report, filename)

        start_file(filename)

    def on_in_report_activate(self, *args):
        from ..reports import month
        import taburet.report.excel
        import tempfile
        from taburet.utils import start_file

        report = month.do(self.bank_acc, self.get_date(), True)
        filename = tempfile.mkstemp('.xls')[1]
        taburet.report.excel.save(report, filename)

        start_file(filename)

    def on_out_report_activate(self, *args):
        from ..reports import month
        import taburet.report.excel
        import tempfile
        from taburet.utils import start_file

        report = month.do(self.bank_acc, self.get_date(), False)
        filename = tempfile.mkstemp('.xls')[1]
        taburet.report.excel.save(report, filename)

        start_file(filename)

    def show_dialog(self, *args):
        from cakeplant.accounts import AccountsForm
        AccountsForm().show()