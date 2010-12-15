import calendar

def get_month_transaction_days(acc, year, month):
    monthdays = calendar.monthrange(year, month)
    result = get_month_transaction_days.db.view(
        'bank/transaction_days', startkey=[acc._id, year, month, 1],
        endkey=[acc._id, year, month, monthdays], group=True, group_level=4).all()

    return [r['key'][-1] for r in result]
