# -*- coding: utf-8 -*-

import taburet.accounts
from datetime import timedelta
from itertools import groupby

from taburet.report import Workbook, group_sum

def fill_transactions(sh, sr, sc, transactions):
    for i, r in enumerate(transactions):
        sh[sr+i:sc+0].value = str(r.num)
        sh[sr+i:sc+1].value = r.account
        sh[sr+i:sc+2].value = r.who
        sh[sr+i:sc+3].value = r.amount
        sh[sr+i:sc+4].value = r.what

def fill_total(sh, r, c, transactions):
    total = sum(r.amount for r in transactions)
    sh[r:c].value = total

def fill_amounts_grouped_by_account(sh, sr, sc, transactions):
    data = {}
    
    for k, g in groupby(transactions, lambda t: t.account):
        group_sum(data, k, sum(r.amount for r in g))

    for i, account in enumerate(sorted(data.keys())):
        sh[sr+i:sc].value = account
        sh[sr+i:sc+2].value = data[account]

def get_transactions(account, date, income=False, outcome=False):
    transactions = account.transactions(date, date, income=income, outcome=outcome).all()
    transactions.sort(key=lambda r: r.num)
    
    for t in transactions:
        if income:
            acc = t.from_acc
        elif outcome:
            acc = t.to_acc
            
        t.account = taburet.accounts.Account.get(acc[-1]).name
        
    return transactions

def do(account, date):
    book = Workbook()
    
    sh = book.add_sheet('касса')

    sh.merge(0,0,0,9).value = date.strftime('Касса за %d %B %Y') 
    
    begin_saldo = account.balance(None, date - timedelta(days=1))
    sh[1:0].value = 'Сальдо на начало %.2f' % begin_saldo.balance
    
    end_saldo = account.balance(None, date)
    sh[1:5].value = 'Сальдо на конец %.2f' % end_saldo.balance
    
    sh.merge(2,2,0,4).value = 'Приход'
    sh.merge(2,2,5,9).value = 'Расход'
    
    sh[2:0].style.align.horz.center()
    sh[2:5].style.align.horz.center()        
    
    for sc in (0, 5):
        sh[3:0+sc].value = '№'
        sh[3:1+sc].value = 'Счет'
        sh[3:2+sc].value = 'Кто'
        sh[3:3+sc].value = 'Сколько'
        sh[3:4+sc].value = 'За что'
    
    in_transactions = get_transactions(account, date, income=True)
    fill_transactions(sh, 4, 0, in_transactions)
    
    out_transactions = get_transactions(account, date, outcome=True)
    fill_transactions(sh, 4, 5, out_transactions)
    
    total_row = sh.maxrow + 1
    
    sh[total_row:0].value = 'ИТОГО'
    fill_total(sh, total_row, 3, in_transactions)
    fill_total(sh, total_row, 8, out_transactions)

    sh.range(2, 3, 0, 4).set_borders()
    sh.range(4, total_row - 1, 0, 4).set_borders()
    sh.range(total_row, total_row, 0, 4).set_borders(0)

    sh.range(2, 3, 5, 9).set_borders()
    sh.range(4, total_row - 1, 5, 9).set_borders()
    sh.range(total_row, total_row, 5, 9).set_borders(0)
    
    fill_amounts_grouped_by_account(sh, total_row + 2, 1, in_transactions)
    fill_amounts_grouped_by_account(sh, total_row + 2, 6, out_transactions)
    
    sh.rows.height = 255

    with sh.style as style:
        style.align.vert.center()
        style.format = '0.00'
    
    for column in (0, 1, 2, 5, 6, 7):
        sh[:column].autofit(3)
        
    return book
