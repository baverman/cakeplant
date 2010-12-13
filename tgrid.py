#!/usr/bin/env python

import gtk
from taburet.ui.grid import GridColumn, Grid, IntGridColumn
from taburet.ui import idle

model = [{'aaa': r, 'bbb': 'wow'} for r in range(50)]
model.append({'aaa':'', 'bbb':''})

window = gtk.Window(gtk.WINDOW_TOPLEVEL)
window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
window.set_position(gtk.WIN_POS_CENTER)
window.set_default_size(100, 400)

sw = gtk.ScrolledWindow()
sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
window.add(sw)

table = Grid(IntGridColumn('aaa'), GridColumn('bbb'))
sw.add(table)
table.set_model(model)
table.show()

w, h = sw.size_request()
window.set_default_size(w, min(max(400, h), 500))
window.show_all()

window.connect('delete-event', lambda *args:gtk.main_quit())

gtk.main()