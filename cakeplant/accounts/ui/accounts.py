from taburet.ui import BuilderAware, join_to_file_dir
from taburet.ui import form

from taburet.accounts import AccountsPlan, accounts_walk

class AccountsForm(BuilderAware):
    """glade-file: accounts.glade"""

    def __init__(self):
        super(AccountsForm, self).__init__(join_to_file_dir(__file__, 'accounts.glade'))
        self.accounts = {}
        self.fill()
        self.init_form()

    def on_commit(self, dr, row):
        row.save()

    def name_changed(self, field, dr):
        it = self.account_store.get_iter(dr.account_path)
        self.account_store.set(it, 1, dr[field.name])

    def desc_changed(self, field, dr):
        it = self.account_store.get_iter(dr.account_path)
        self.account_store.set(it, 2, dr[field.name])

    def init_form(self):
        self.dr = form.DirtyRow([
            form.Field('name', self.name_entry, on_change=self.name_changed),
            form.Field('desc', self.desc_entry, on_change=self.desc_changed)],
            self.on_commit
        )

    def fill(self):
        roots = {0:None}
        node = None
        plevel = 0
        for level, acc in accounts_walk(AccountsPlan().accounts()):
            self.accounts[acc.id] = acc
            if level > plevel:
                roots[level] = node

            node = self.account_store.append(roots[level], (acc.id, acc.name, acc.desc))
            plevel = level

        self.account_view.expand_all()
        self.window.set_default_size(-1, max(400, min(500, self.account_view.size_request()[1])))

    def show(self):
        self.window.show_all()

    def update_form(self, path):
        if self.dr.set_row(self.accounts[self.account_store[path][0]]):
            self.dr.account_path = path

    def on_account_view_cursor_changed(self, view):
        path, _ = view.get_cursor()
        self.update_form(path)

    def on_account_view_row_activated(self, view, path, column):
        self.update_form(path)
        self.name_entry.grab_focus()