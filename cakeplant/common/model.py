from couchdbkit import ( Document, ListProperty, FloatProperty, ResourceNotFound, ResourceConflict,
    IntegerProperty, StringProperty)

from taburet.cdbkit import DateTimeProperty

from datetime import datetime

class Customer(Document):
    NotFound = ResourceNotFound

    name = StringProperty(required=True)
    address = StringProperty(required=False)
    inn = StringProperty(required=False)
    points = ListProperty(default=[]) # id, name

    def add_point(self, name):
        id = max(p['id'] for p in self.points) + 1
        self.points = {'id':id, 'name':name}

    def __repr__(self):
        if 'hidden' not in self or not self.hidden:
            return "<%s>" % self.name.encode('utf8')
        else:
            return "<@ %s>" % self.name.encode('utf8')


class Price(Document):
    good = StringProperty(required=True)
    type = StringProperty(required=True)
    start_at = DateTimeProperty(required=True)


class PriceType(Document):
    name = StringProperty(required=True)
    point = StringProperty(required=True)
    start_at = DateTimeProperty(required=True)


class PointWay(Document):
    point = StringProperty(required=True)
    way = StringProperty(required=True)