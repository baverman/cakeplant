# -*- coding: utf-8 -*-
from datetime import datetime

import gtk, pango

from taburet.ui import BuilderAware, join_to_file_dir, idle
from taburet.ui.completion import Completion
from taburet.ui.grid import Grid, IntGridColumn, FloatGridColumn, DirtyRow as GridDirtyRow

from taburet.doctype import get_by_type
from cakeplant.common import Customer
from ..model import get_month_consignment_days, get_day_consignment_customers, get_consignments

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
            return

        for i, c in enumerate(consigments):
            sw = gtk.ScrolledWindow()
            sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)

            gr = Grid([
                IntGridColumn('id', label='Наименование', width=40),
                FloatGridColumn('count', label='Кол-во', width=7, format="%g"),
                FloatGridColumn('price', label='Цена', width=7),
            ])
            dr = GridDirtyRow(gr)
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