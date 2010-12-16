import calendar

db = [None]

def get_month_transaction_days(acc, year, month):
    monthdays = calendar.monthrange(year, month)
    result = db[0].view('bank/transaction_days', startkey=[acc._id, year, month, 1],
        endkey=[acc._id, year, month, monthdays], group=True, group_level=4).all()

    return [r['key'][-1] for r in result]

def get_what_choice():
    result = db[0].view('bank/what_choice', group=True)
    return [r['key'] for r in result]

def get_who_choice():
    result = db[0].view('bank/who_choice', group=True)
    return [r['key'] for r in result]