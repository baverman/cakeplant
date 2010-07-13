# -*- coding: utf-8 -*-

from taburet.utils import sync_design_documents
import taburet.accounting

import couchdbkit
import csv, datetime

s = couchdbkit.Server()
db = s.get_or_create_db('demo')

sync_design_documents(db, ('taburet.counter', 'taburet.accounting'))
taburet.accounting.set_db_for_models(db)

plan = taburet.accounting.model.AccountsPlan()
def get_or_create_account(name):
    result = plan.get_by_name(name)
    if result:
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

data = csv.reader(open('TData.csv', 'rb'))

bank = get_or_create_account('51/1')

header = True
for r in data:
    if header:
        header = False
        continue
    date = datetime.datetime.strptime(r[0], "%m/%d/%y %H:%M:%S")
    if date.year < 2010:
        continue
    
    inout = int(r[1])
    what = r[2].decode('utf-8')
    how = float(r[3])
    num = int(r[4])
    kuda = r[5]
    who = fam_hash[int(r[6])]
    
    acc = get_or_create_account(kuda)
    
    if inout == 1:
        tran = plan.create_transaction(acc, bank, how, date)
    else:
        tran = plan.create_transaction(bank, acc, how, date)
        
    tran.what = what
    tran.who = who
    tran.num = num
    
    tran.save()  