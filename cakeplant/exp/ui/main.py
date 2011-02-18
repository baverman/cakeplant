# -*- coding: utf-8 -*-
from datetime import datetime

import gtk, pango

from taburet.ui import BuilderAware, join_to_file_dir, idle
from taburet.ui.completion import Completion
from taburet.ui.grid import Grid, GridColumn, FloatGridColumn, DirtyRow as GridDirtyRow

from taburet.doctype import get_by_type
from cakeplant.common import Customer, Good
from ..model import get_month_consignment_days, get_day_consignment_customers, get_consignments

def get_goods(cache={}):
    if not cache:
        for g in get_by_type(Good):
            gid = g._id.rpartition('-')[2]
            cache[gid] = g

    return cache

def get_goods_list(cache=[]):
    if not cache:
        for r in sorted(((k, v.fullname, v.fullname.lower())
                for k, v in get_goods().iteritems()), key=lambda r: r[1]):
            cache.append(r)

    return cache

class GoodColumn(GridColumn):
    def __init__(self, attr, **kwargs):
        GridColumn.__init__(self, attr, **kwargs)
        self.completion = Completion(gtk.ListStore(str, str))

        self.completion.on_fill = self.completion_fill
        self.completion.on_select = self.completion_select

        column = self.completion.column
        cell = gtk.CellRendererText()
        column.pack_start(cell)
        column.set_attributes(cell, text=0)

        cell = gtk.CellRendererText()
        column.pack_start(cell)
        column.set_attributes(cell, text=1)

    def completion_select(self, entry, model, iter, final):
        entry.good_id = int(model.get_value(iter, 0))
        entry.set_text(model.get_value(iter, 1))
        entry.set_position(-1)

    def completion_fill(self, model, key):
        added = {}
        if not key:
            return

        key = unicode(key, 'utf-8').lower()

        for k, fn, lfn in get_goods_list():
            kkk = (k, fn)
            if kkk not in added and (
                    key == '*' or lfn.startswith(key) or k.startswith(key) ):
                added[kkk] = True
                model.append(kkk)

        for k, fn, lfn in get_goods_list():
            kkk = (k, fn)
            if kkk not in added and ( key == '*' or key in lfn ):
                model.append(kkk)

    def update_row_value(self, dirty_row, row):
        value = dirty_row[self.name]
        row[self.name] = int(value)

    def _set_value(self, entry, row):
        value = row[self.name]
        with self.completion.block(entry):
            if value is None:
                entry.set_text('')
            else:
                entry.set_text(get_goods()[str(value)].fullname)
        entry.good_id = value

    def _set_dirty_value(self, entry, row):
        self._set_value(entry, row)

    def get_dirty_value(self, entry):
        return entry.good_id

    def create_widget(self, *args):
        w = super(GoodColumn, self).create_widget(*args)
        self.completion.attach_to_entry(w)
        return w

class ForwarderForm(BuilderAware):
    """glade-file: main.glade"""

    def __init__(self, conf):
        BuilderAware.__init__(self, join_to_file_dir(__file__, 'main.glade'))
        self.conf = conf
        self.prepare_customers_selector()
        self.current_point = None

    def prepare_customers_selector(self):
        self.customers_completion = Completion(gtk.ListStore(str, int, object))
        self.customers_completion.on_fill = self.fill_customers
        self.customers_completion.on_select = self.select_customer

        column = self.customers_completion.column
        cell = gtk.CellRendererText()
        column.pack_start(cell)
        column.set_attributes(cell, text=0, weight=1)

        self.customers_completion.attach_to_entry(self.customer_selector)

        self.customers = []
        for c in get_by_type(Customer):
            for p in c.points:
                self.customers.append((c.name + ' ' + p['name'], c.get_point_id(p['id'])))

        self.customers.sort(key=lambda r:r[0])
        self.today_customers = {}

    def fill_customers(self, model, key):
        if not key:
            return

        key = unicode(key, 'utf-8').lower()
        for name, id in self.customers:
            if key == '*' or key in name.lower():
                w = pango.WEIGHT_BOLD if id in self.today_customers else pango.WEIGHT_NORMAL
                model.append((name, w, id))

    def select_customer(self, entry, model, iter, final):
        entry.set_text(model.get_value(iter, 0))
        entry.set_position(-1)
        if final:
            self.customer_lb.set_text(model.get_value(iter, 0))
            self.current_point = model.get_value(iter, 2)
            self.update_consigment_grid()

    def update_consigment_grid(self):
        self.cons_nb.hide()
        for i in range(self.cons_nb.get_n_pages()):
            self.cons_nb.remove_page(-1)

        dt = self.get_date()
        consigments = get_consignments(dt, self.current_point)

        if not consigments:
            self.cons_are_out_lb.show()
            return

        self.cons_are_out_lb.hide()

        def new():
            return {'id':None, 'count':0, 'price':0.0, '_isnew_':True}

        for i, c in enumerate(consigments):
            sw = gtk.ScrolledWindow()
            sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)

            def make_on_commit(cons):
                def inner(dr, row):
                    if '_isnew_' in row:
                        del row['_isnew_']
                        isnew = True
                    else:
                        isnew = False

                    cons.positions[:] = [r for r in cons.positions if '_isnew_' not in r]
                    cons.save()

                    cons.positions.append(new())

                    if isnew:
                        dr.jump_to_new_row(0)

                return inner

            gr = Grid([
                GoodColumn('id', label='Наименование', width=40),
                FloatGridColumn('count', label='Кол-во', width=7, format="%g"),
                FloatGridColumn('price', label='Цена', width=7),
            ])

            dr = GridDirtyRow(gr, make_on_commit(c))
            c.positions.append(new())
            gr.set_model(c.positions, dr)
            sw.add(gr)
            sw.show_all()

            self.cons_nb.append_page(sw, gtk.Label('Накладная #%d' % (i + 1)))

        self.cons_nb.show()

    def show(self):
        self.window.show()
        self.update_consignment_days()

    def update_consignment_days(self):
        self.calendar.clear_marks()

        def update():
            date = self.get_date()
            map(self.calendar.mark_day, get_month_consignment_days(date.year, date.month))

        idle(update)

    def update_today_customers(self):
        self.today_customers = dict((r, True) for r in get_day_consignment_customers(self.get_date()))

    def on_calendar_month_changed(self, *args):
        self.update_consignment_days()

    def on_calendar_day_selected(self, *args):
        idle(self.update_today_customers)
        if self.current_point:
            self.update_consigment_grid()

    def set_date(self, date):
        self.calendar.props.year = date.year
        self.calendar.props.month = date.month - 1
        self.calendar.props.day = date.day

    def get_date(self):
        return datetime(self.calendar.props.year,
            self.calendar.props.month + 1, self.calendar.props.day)

    def on_window_delete_event(self, *args):
        gtk.main_quit()