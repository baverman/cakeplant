# -*- coding: utf-8 -*-

from taburet.accounts import AccountsPlan, Account
from taburet import PackageManager

import couchdbkit
import csv, datetime
import sys

s = couchdbkit.Server()
db = s.get_or_create_db('dalxleb')
pm = PackageManager()
pm.use('taburet.accounts')
pm.set_db(db, 'taburet.accounts', 'taburet.transactions')
pm.sync_design_documents()


accounts_cache = {}

plan = AccountsPlan()
def get_or_create_account(name):
    try:
        return accounts_cache[name]
    except KeyError:
        pass

    result = plan.get_by_name(name)
    if result:
        accounts_cache[name] = result
        return result

    if '/' in name:
        parent, _child = name.split('/', 1)
        return plan.add_account(name, get_or_create_account(parent))

    return plan.add_account(name)


fam_hash = {}
fams = csv.reader(open('TFams.csv', 'rb'))
header = True
for r in fams:
    if header:
        header = False
        continue

    id = int(r[0])

    fam_hash[id] = r[1].decode('utf8')


k_hash = {}
fams = csv.reader(open('TKassy.csv', 'rb'))
header = True
for r in fams:
    if header:
        header = False
        continue

    id = int(r[0])
    date = datetime.datetime.strptime(r[1], "%m/%d/%y %H:%M:%S")
    k_hash[id] = date


bank = get_or_create_account(sys.argv[1])

def read_transaction(data, inout):
    header = True
    for r in data:
        if header:
            header = False
            continue

        date = k_hash[int(r[0])]
        if date.year < 2010:
            continue

        what = r[1].decode('utf-8')
        how = float(r[2]) if r[2] else 0.0
        num = int(r[3])
        kuda = r[4]

        try:
            who = fam_hash[int(r[5])] if r[5] else u'Неизвестный'
        except KeyError:
            who = u'Неизвестный'
            print u'Error who', r

        if not kuda:
            print 'Error account', r
            continue

        acc = get_or_create_account(kuda)

        if inout:
            tran = plan.create_transaction(acc, bank, how, date)
        else:
            tran = plan.create_transaction(bank, acc, how, date)

        tran.what = what
        tran.who = who
        tran.num = num

        tran.save()

read_transaction(csv.reader(open('TIn.csv', 'rb')), True)
read_transaction(csv.reader(open('TOut.csv', 'rb')), False)