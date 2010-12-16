# -*- coding: utf-8 -*-
import gtk

from taburet.ui.feedback import show_message

from taburet.ui import BuilderAware, join_to_file_dir, idle, refresh_gui
from taburet.ui.grid import (Grid, GridColumn, BadValueException,
    IntGridColumn, FloatGridColumn, DirtyRow, AutocompleteColumn)

from taburet.transactions import Transaction
from taburet.accounts import AccountsPlan, accounts_walk

from .. import get_who_choice, get_what_choice

class AccountColumn(GridColumn):
    def __init__(self, attr, choices, **kwargs):
        GridColumn.__init__(self, attr, **kwargs)
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

class TransactionsForm(BuilderAware):
    """glade-file: transactions.glade"""
    def __init__(self, inout, other_account, date, last_in, last_out, on_close=None):
        BuilderAware.__init__(self, join_to_file_dir(__file__, "transactions.glade"))
        self.on_close = on_close

        transactions = sorted(other_account.transactions(
            date, date, income=inout, outcome=not inout), key=lambda r: r.num)

        last = last_in if inout else last_out

        def new():
            tran = Transaction()
            tran.what = ''
            tran.who = ''
            tran.date = date

            tran._isnew_ = True

            if inout:
                tran.to_acc = other_account.account_path
            else:
                tran.from_acc = other_account.account_path

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

        choices = [(r._id, r.name) for _, r in accounts_walk(AccountsPlan().accounts(), True)]

        columns = [
            IntGridColumn('num', label='№', editable=False, width=3),
            AccountColumn('from_acc' if inout else 'to_acc', choices, label='Счет', width=4),
            AutocompleteColumn('who', get_who_choice(), label='Контрагент', width=15),
            FloatGridColumn('amount', label='Сколько', width=7),
            AutocompleteColumn('what', get_what_choice(), label='За что', width=10),
        ]

        self.tv = Grid(columns)
        self.sw.add(self.tv)

        transactions.append(new())
        self.tv.set_model(transactions, DirtyRow(self.tv, on_commit, on_error))
        self.tv.show_all()

    def show(self):
        self.window.show_all()
        refresh_gui()
        idle(self.tv.set_cursor, len(self.tv.model) - 1, 1)

    def on_window_delete_event(self, *args):
        if self.on_close:
            self.on_close()