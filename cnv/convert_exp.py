# -*- coding: utf-8 -*-
import sys, time
import csv, datetime
import cPickle

import couchdbkit
from taburet import PackageManager

from cakeplant.exp import Consignment
from cakeplant.common import Customer

s = couchdbkit.Server()
prefix = sys.argv[1]

pm = PackageManager()
pm.use('cakeplant.exp')
pm.set_db(s.get_or_create_db(prefix + '_exp'), 'cakeplant.exp')
pm.set_db(s.get_or_create_db(prefix + '_common'), 'cakeplant.common')
pm.sync_design_documents()

def traverse(filename):
    header = True
    for r in csv.reader(open(filename, 'rb')):
        if header:
            header = False
            continue

        yield r

def parse_date(dt):
    return datetime.datetime.strptime(dt, "%m/%d/%y %H:%M:%S")

def dump_orders(oldzacs):
    result = {}

    for id, date, idZac, num, driver, idWay, exp, _, _ in traverse('TOrders.csv'):
        if idZac not in oldzacs:
            continue

        try:
            date = parse_date(date)
        except ValueError:
            continue

        if date < datetime.datetime(2010, 11, 1):
            continue

        result[id] = (date, oldzacs[idZac], num, driver, idWay, exp)

    cPickle.dump(result, open('orders.pickle', 'w'))
    return result

def process_order_data(orders):
    counter = 0
    result = {}
    for id, idGood, idPrice, Exit, price, count, _ in traverse('TOrData.csv'):
        if id not in orders:
            continue

        try:
            result.setdefault(id, []).append((int(idGood), float(count), float(price)))
        except ValueError:
            continue

        counter += 1
        if counter % 10000 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()

    cPickle.dump(result, open('ordata.pickle', 'w'))
    return result

def create_order(date, idZac, num, driver, idWay, exp):
    try:
        num = int(num)
    except ValueError:
        num = 0

    return Consignment(num=num, date=date,
        forwarder=exp.decode('utf8'), way=idWay.decode('utf8'),
        driver=driver.decode('utf8'), dest=list(idZac))

def make_orders(orders, ordata):
    counter = 0
    orders_to_save = []

    for id, positions in ordata.iteritems():
        order = create_order(*orders[id])
        [order.add_position(*v) for v in positions]
        orders_to_save.append(order)

        if len(orders_to_save) > 500:
            Consignment.get_db().save_docs(orders_to_save, all_or_nothing=True)
            Consignment.get_db().ensure_full_commit()
            orders_to_save[:] = []

        counter += 1
        if counter % 10000 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()

    if len(orders_to_save):
        Consignment.get_db().save_docs(orders_to_save, all_or_nothing=True)
        Consignment.get_db().ensure_full_commit()
        orders_to_save[:] = []

def make_customers():
    zacs = {}
    for idFirm, name, point, idWay, copies, id, NDS, idPrice, isVisible in traverse('TZacs.csv'):
        if idFirm == '1':
            zacs[id] = point, isVisible

    c2z = {}
    for pid, zid in traverse('TPoksZacs.csv'):
        c2z.setdefault(pid, []).append(zid)

    oldzacs = {}
    customers = {}
    for id, adress, inn, name, visible in traverse('TPocs.csv'):
        if not name:
            name = 'Unknown'

        c = Customer(_id='c-' + id, name=name.decode('utf-8'),
            address=adress.decode('utf-8'), inn=inn.decode('utf-8'))

        if visible == '0':
            c.hidden = True

        customers[int(id)] = c

        if id in c2z:
            for i, zid in enumerate(c2z[id]):
                if zid not in zacs:
                    print "Can't find zid", zid, 'for customer', id, name, visible
                    continue

                pname, visible = zacs[zid]
                p = {'id':i+1, 'name':pname.decode('utf-8')}
                if visible == '0':
                    p['hidden'] = True
                c.points.append(p)

                if zid in oldzacs:
                    print 'zac', zid, 'already in map', c, ' -> ', customers[oldzacs[zid][0]]
                    continue

                oldzacs[zid] = (int(id), p['id'])

        c.save()

    cPickle.dump(oldzacs, open('oldzacs.pickle', 'w'))
    return oldzacs

#make_customers()
dump_orders(cPickle.load(open('oldzacs.pickle')))
process_order_data(cPickle.load(open('orders.pickle')))
make_orders(cPickle.load(open('orders.pickle')), cPickle.load(open('ordata.pickle')))

