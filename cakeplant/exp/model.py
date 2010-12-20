from couchdbkit import ( Document, ListProperty, FloatProperty, ResourceNotFound, ResourceConflict,
    IntegerProperty, StringProperty)

from taburet.cdbkit import DateTimeProperty

from datetime import datetime

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