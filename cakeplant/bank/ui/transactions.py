# -*- coding: utf-8 -*-
import gtk

from taburet.ui.feedback import show_message

from taburet.ui import (BuilderAware, join_to_file_dir, idle, refresh_gui, guard, guarded_by,
    create_calendar_dialog)

from taburet.ui.grid import (Grid, GridColumn, BadValueException,
    IntGridColumn, FloatGridColumn, DirtyRow, AutocompleteColumn)

from taburet.ui.completion import make_simple_completion

from taburet.transactions import Transaction
from taburet.accounts import AccountsPlan, accounts_walk

from .. import get_who_choice, get_what_choice

class AccountColumn(GridColumn):
    def __init__(self, attr, choices, **kwargs):
        GridColumn.__init__(self, attr, **kwargs)
        self.choices = choices
        self.completion_choices = [v for k, v in self.choices]
        self.completion = make_simple_completion(self.completion_choices)

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
        self.completion.attach_to_entry(w)
        return w

class CheckBoxColumn(GridColumn):
    def __init__(self, model, on_check=None):
        GridColumn.__init__(self, 'checked_state')
        self.model = model
        self.checks = {}
        self.dr = None
        self.on_check = on_check

    def create_widget(self, dirty_row):
        e = gtk.CheckButton()
        e.props.can_focus = False
        e.connect_after('clicked', self.on_clicked)
        self.dr = dirty_row
        return e

    @guarded_by('changing')
    def on_clicked(self, chk):
        self.checks[self.model[chk.row]._id] = chk.get_active()
        self.emit_check()

    def emit_check(self):
        if self.on_check:
            self.on_check(self.checks)

    def on_all_clicked(self, chk):
        self.checks.clear()

        if chk.get_active():
            for r in self.model:
                self.checks[r._id] = True

        self.emit_check()
        self.dr.grid.refresh()

    @guard('changing')
    def set_value(self, entry, row):
        entry.set_active(self.checks.get(row._id, False))

    def get_title_widget(self):
        w = gtk.CheckButton()
        w.props.can_focus = False
        w.connect_after('clicked', self.on_all_clicked)
        return w

    def get_attach_flags(self):
        return 0

    @property
    def checked_rows(self):
        for r in self.model[:]:
            if r._id and self.checks.get(r._id, False):
                yield r

    def clear(self):
        self.checks.clear()
        self.emit_check()


class TransactionsForm(BuilderAware):
    """glade-file: transactions.glade"""
    def __init__(self, inout, other_account, date, last_in, last_out, on_close=None):
        BuilderAware.__init__(self, join_to_file_dir(__file__, "transactions.glade"))
        self.on_close = on_close
        self.date = date

        self.transactions = transactions = sorted(other_account.transactions(
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
                dr.jump_to_new_row(2)

        def on_error(dr, e):
            show_message(self.sw, str(e), 5000)

        def on_check(checks):
            for k, v in checks.iteritems():
                if k and v:
                    self.delete_btn.set_sensitive(True)
                    self.move_btn.set_sensitive(True)
                    return

            self.delete_btn.set_sensitive(False)
            self.move_btn.set_sensitive(False)


        choices = [(r._id, r.name) for _, r in accounts_walk(AccountsPlan().accounts(), True)]

        self.check_col = CheckBoxColumn(transactions, on_check)

        columns = [
            self.check_col,
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

        self.window.set_title(('Приход за ' if inout else 'Расход за ') + date.strftime('%d.%m.%Y'))

    def show(self):
        self.window.show_all()
        refresh_gui()
        idle(self.tv.set_cursor, len(self.tv.model) - 1, 1)

    def on_window_delete_event(self, *args):
        if self.on_close:
            self.on_close()

    def on_move_btn_clicked(self, btn):
        dlg = create_calendar_dialog(parent=self.window, date=self.date)

        if dlg.run() == gtk.RESPONSE_APPLY:
            dt = dlg.get_date()
            for r in self.check_col.checked_rows:
                if self.date.date() != dt.date():
                    self.transactions.remove(r)
                r.date = dt
                r.save()

            self.check_col.clear()
            self.tv.refresh()

        dlg.destroy()

    def on_delete_btn_clicked(self, btn):
        dlg = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION,
            gtk.BUTTONS_YES_NO, "Удалить выделенные проводки?")

        if dlg.run() == gtk.RESPONSE_YES:
            for r in self.check_col.checked_rows:
                self.transactions.remove(r)
                r.delete()

            self.check_col.clear()
            self.tv.refresh()

        dlg.destroy()