import calendar

def make_month_transaction_days_getter(db):
    def inner(acc, year, month):
        monthdays = calendar.monthrange(year, month)
        result = db.view('bank/transaction_days', startkey=[acc._id, year, month, 1],
            endkey=[acc._id, year, month, monthdays], group=True, group_level=4).all()

        return [r['key'][-1] for r in result]

    return inner