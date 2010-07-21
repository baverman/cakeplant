# -*- coding: utf-8 -*-

import taburet.utils
import taburet.accounting
from datetime import timedelta
from itertools import groupby

from taburet.report import Workbook

def fill_transactions(sh, sr, sc, pivot, days):
    for d, c in days.items():
        sh[sr:sc + 2 + c].value = str(d)

    with sh.range(sr, sr, sc + 2, sc + 1 + len(days)).style as style:
        style.align.horz.center()
    
    sh[sr:sc+0].set_borders()
    sh[sr:sc+1].set_borders()
    sh.range(sr, sr, sc + 2, sc + 1 + len(days)).set_borders()
    
    i = sr + 1
    for acc in sorted(pivot.keys()):
        sh[i:sc+0].value = acc
        start = i
        for who in sorted(pivot[acc].keys()):
            sh[i:sc+1].value = who
            for day, amount in pivot[acc][who].items():
                sh[i:sc + 2 + days[day]].value = amount
                
            i += 1

        sh.range(start, i - 1, 0, 0).set_borders(0)
        sh.range(start, i - 1, 1, 1).set_borders()
        sh.range(start, i - 1, 2, 1 + len(days)).set_borders()
    
    return i - 1

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
        aname = taburet.accounting.Account.get(account).name
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
    
    fill_transactions(sh, 2, 0, pivot, days)
    
    with sh.style as style:
        style.align.vert.center()
        style.format = '0.00'
    
    sh.rows.height = 255
    sh[:0].autofit(3)
    sh[:1].autofit(3)
    
    return book