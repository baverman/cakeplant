# -*- coding: utf-8 -*-

from pyExcelerator import Workbook
import taburet.accounting
from datetime import timedelta
from itertools import groupby

def fill_transactions(sh, sr, sc, transactions):
    for i, r in enumerate(transactions):
        sh.write(sr+i, sc+0, r.num)
        sh.write(sr+i, sc+1, r.account)
        sh.write(sr+i, sc+2, r.who)
        sh.write(sr+i, sc+3, r.amount)
        sh.write(sr+i, sc+4, r.what)
    
    return sr + i

def fill_total(sh, r, c, transactions):
    total = sum(r.amount for r in transactions)
    sh.write(r, c, u'%.2f' % total)

def fill_amounts_grouped_by_account(sh, sr, sc, transactions):
    data = {}
    
    for k, g in groupby(transactions, lambda t: t.account):
        data[k] = sum(r.amount for r in g)    

    for i, account in enumerate(sorted(data.keys())):
        sh.write(sr+i, sc, account)
        sh.write(sr+i, sc+2, data[account])


def get_transactions(account, date, income=False, outcome=False):
    transactions = account.transactions(date, date, income=income, outcome=outcome).all()
    transactions.sort(key=lambda r: r.num)
    
    for t in transactions:
        if income:
            acc = t.from_acc
        elif outcome:
            acc = t.to_acc
            
        t.account = taburet.accounting.Account.get(acc[-1]).name
        
    return transactions

def do(account, date, filename):
    book = Workbook()
    
    sh = book.add_sheet(u'касса')

    begin_saldo = account.balance(None, date - timedelta(days=1))
    end_saldo = account.balance(None, date)

    
    sh.write_merge(0,0,0,9, date.strftime('Касса за %d %B %Y').decode('utf8'))
    sh.write(1,0, u'Сальдо на начало %.2f' % begin_saldo.balance)
    sh.write(1,5, u'Сальдо на конец %.2f' % end_saldo.balance)
    
    sh.write_merge(2,2,0,4, u'Приход')
    sh.write_merge(2,2,5,9, u'Расход')
    
    sh.write(3, 0, u'№')
    sh.write(3, 1, u'Счет')
    sh.write(3, 2, u'Кто')
    sh.write(3, 3, u'Сколько')
    sh.write(3, 4, u'За что')
    
    sh.write(3, 5, u'№')
    sh.write(3, 6, u'Счет')
    sh.write(3, 7, u'Кто')
    sh.write(3, 8, u'Сколько')
    sh.write(3, 9, u'За что')
    
    in_transactions = get_transactions(account, date, income=True)
    i1 = fill_transactions(sh, 4, 0, in_transactions)
    
    out_transactions = get_transactions(account, date, outcome=True)
    i2 = fill_transactions(sh, 4, 5, out_transactions)
    
    total_row = max(i1, i2) + 1
    
    sh.write(total_row, 0, u'ИТОГО')
    fill_total(sh, total_row, 3, in_transactions)
    fill_total(sh, total_row, 8, out_transactions)
    
    fill_amounts_grouped_by_account(sh, total_row + 2, 1, in_transactions)
    fill_amounts_grouped_by_account(sh, total_row + 2, 6, out_transactions)
    
    book.save(filename)