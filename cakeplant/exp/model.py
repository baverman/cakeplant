from couchdbkit import ( Document, ListProperty, FloatProperty, ResourceNotFound, ResourceConflict,
    IntegerProperty, StringProperty)

from taburet.cdbkit import DateTimeProperty

class IntListProperty(ListProperty):
    def __init__(self, verbose_name=None, default=None,
            required=False, **kwds):
        super(IntListProperty, self).__init__(verbose_name=verbose_name,
            default=default, required=required, item_type=int, **kwds)


class Consignment(Document):
    NotFound = ResourceNotFound

    num = IntegerProperty(required=True)
    date = DateTimeProperty(required=True)
    forwarder = StringProperty(required=True)
    way = StringProperty(required=True)
    driver = StringProperty(required=True)

    dest = IntListProperty(required=True)

    positions = ListProperty(default=[]) # id, count, price

    def add_position(self, good_id, count, price):
        self.positions.append({'id':int(good_id), 'count':float(count), 'price':float(price)})

    def __repr__(self):
        return "<#%d %s %s %f>" % (self.num, str(self.date), str(self.dest), self.summ)

    @property
    def summ(self):
        return sum(p['price']*p['count'] for p in self.positions)

def get_month_consignment_days(year, month):
    result = Consignment.get_db().view('exp/consignment_days', startkey=[year, month],
        endkey=[year, month, {}], group=True, group_level=3)

    return [r['key'][-1] for r in result]

def get_day_consignment_customers(dt):
    result = Consignment.get_db().view('exp/consignment_days', startkey=[dt.year, dt.month, dt.day],
        endkey=[dt.year, dt.month, dt.day, {}], group=True, group_level=5)

    return [tuple(r['key'][-2:]) for r in result]

def dt2int(dt):
    return int(dt.strftime('%Y%m%d'))

def get_consignments(dt, point_id=None):
    return Consignment.view('exp/get_consignments',
        key=[dt2int(dt), point_id[0], point_id[1]], include_docs=True).all()