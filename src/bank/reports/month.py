# -*- coding: utf-8 -*-

import taburet.utils
import taburet.accounts
from datetime import timedelta
from itertools import groupby

from taburet.report import Workbook, group_sum

def fill_transactions(sh, sr, pivot, days):
    last_column = 1 + len(days)
    for d, c in days.items():
        sh[sr:2 + c].value = str(d)

    sh.range(sr, sr, 2, last_column).style.align.horz.center()
    
    sh[sr:0].set_borders()
    sh[sr:1].set_borders()
    sh.range(sr, sr, 2, last_column).set_borders()
    
    sh[sr:last_column+1].value = 'Итого'
    sh[sr:last_column+1].set_borders()
    
    days_totals = {}
    
    i = sr + 1
    for acc in sorted(pivot.keys()):
        sh[i:0].value = acc
        start = i
        acc_total = 0
        for who in sorted(pivot[acc].keys()):
            sh[i:1].value = who
            who_total = 0
            for day, amount in pivot[acc][who].items():
                acc_total += amount
                who_total += amount
                
                group_sum(days_totals, day, amount)
                
                sh[i:2 + days[day]].value = amount
                
            sh[i:last_column+1].value = who_total
                
            i += 1
        
        if len(pivot[acc]) > 1:
            sh[i-1:last_column+2].value = acc_total

        sh.range(start, i - 1, 0, 0).set_borders(0)
        sh.range(start, i - 1, 1, 1).set_borders()
        sh.range(start, i - 1, 2, last_column).set_borders()
        sh.range(start, i - 1, last_column + 1, last_column + 1).set_borders()
    
    # fill total_row
    
    sh[i:0].value = 'Итого'
    sh[i:last_column + 1].value = sum(days_totals.values())
    
    sh.range(i,i,0,1).set_borders(0)
    sh.range(i, i, 2, last_column).set_borders()
    sh[i:last_column+1].set_borders()
    
    for day, amount in days_totals.items():
        sh[i:2 + days[day]].value = amount    

def fill_total(sh, r, c, transactions):
    total = sum(r.amount for r in transactions)
    sh.write(r, c, total)

def get_pivot(account, date_from, date_to, inout):
    data = account.transactions(date_from, date_to, income=inout, outcome=not inout).all()

    accounts = {}
    days = {}
    
    for t in data:
        t.account = t.from_acc[-1] if inout else t.to_acc[-1] 
    
    # Собираем итоговую таблицу по трем группировкам
    # По счету, по контрагенту и по дню месяца
    for account, g in groupby(data, lambda t: t.account):
        aname = taburet.accounts.Account.get(account).name
        for who, gg in groupby(g, lambda t: t.who):
            for day, ggg in groupby(gg, lambda t: t.date.day):
                days[day] = True
                accounts.setdefault(aname, {}).setdefault(who, {})[day] = sum(t.amount for t in ggg) 
            
    days_indexes = dict((day, i) for i, day in enumerate(sorted(days.keys())))
    
    return accounts, days_indexes

def do(account, date, inout):
    book = Workbook()

    sh = book.add_sheet('касса')

    sh[0:0].value =  date.strftime(('Приход' if inout else 'Расход') + ' за %B %Y')

    date_from, date_to = taburet.utils.month_date_range(date)

    begin_saldo = account.balance(None, date_from - timedelta(days=1))
    sh[1:0].value = 'Сальдо на начало %.2f' % begin_saldo.balance
    
    end_saldo = account.balance(None, date_to)
    sh[1:5].value = 'Сальдо на конец %.2f' % end_saldo.balance
    
    sh[2:0].value = 'Счет'
    sh[2:1].value = 'Контрагент'
    
    pivot, days = get_pivot(account, date_from, date_to, inout)
    
    fill_transactions(sh, 2, pivot, days)
    
    with sh.style as style:
        style.align.vert.center()
        style.format = '0.00'
    
    sh.rows.height = 255
    sh[:0].autofit(3)
    sh[:1].autofit(3)
    
    return book
