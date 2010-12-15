# -*- coding: utf-8 -*-
from taburet.ui import BuilderAware, join_to_file_dir
from taburet.ui import form

from taburet.accounts import AccountsPlan, accounts_walk, Account
from taburet.counter import save_model_with_autoincremented_id

class AccountsForm(BuilderAware):
    """glade-file: accounts.glade"""

    def __init__(self):
        super(AccountsForm, self).__init__(join_to_file_dir(__file__, 'accounts.glade'))
        self.accounts = {}
        self.fill()
        self.init_form()

    def on_commit(self, dr, row):
        path = dr.account_path
        if row._id:
            row.save()
        else:
            save_model_with_autoincremented_id(row, 'acc')
            self.account_store[path][0] = row.id
            self.add_new_account(path)

    def update_tree_view_value(self, field, dr):
        columns = {'name':1, 'desc':2}
        it = self.account_store.get_iter(dr.account_path)
        self.account_store.set(it, columns[field.name], dr[field.name])

    def init_form(self):
        self.dr = form.DirtyRow([
            form.Field('name', self.name_entry, on_change=self.update_tree_view_value),
            form.Field('desc', self.desc_entry, on_change=self.update_tree_view_value)],
            self.on_commit
        )

    def fill(self):
        roots = {0:None}
        node = None
        plevel = 0
        plan = AccountsPlan()
        for level, acc in accounts_walk(plan.accounts()):
            if level > plevel:
                roots[level] = node

            node = self.account_store.append(roots[level], (acc.id, acc.name, acc.desc))
            self.accounts[self.account_store.get_path(node)] = acc
            plevel = level

        def add_new(rows):
            if not rows:
                return

            for p in rows:
                if self.account_store.iter_has_child(p.iter):
                    self.account_view.expand_row(p.path, False)

                add_new(list(p.iterchildren()))
                self.add_new_account(p.path)

        add_new(list(self.account_store))
        self.add_new_account(None)
        self.window.set_default_size(-1, max(200, min(400, self.account_view.size_request()[1])))

    def add_new_account(self, root):
        a = Account(name=u'Новый счет')
        rootiter = None

        if root:
            a.parents=self.accounts[root].account_path
            rootiter = self.account_store.get_iter(root)

        node = self.account_store.append(rootiter, (a.id, a.name, a.desc))
        self.accounts[self.account_store.get_path(node)] = a

    def show(self):
        self.window.show_all()

    def update_form(self, path):
        if self.dr.set_row(self.accounts[path]):
            self.dr.account_path = path

    def on_account_view_cursor_changed(self, view):
        path, _ = view.get_cursor()
        self.update_form(path)

    def on_account_view_row_activated(self, view, path, column):
        self.update_form(path)
        self.name_entry.grab_focus()