import datetime
from flask import Flask, request, jsonify, make_response, Blueprint, abort
from flask_sqlalchemy import SQLAlchemy
from os import environ
import sqlalchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DB_URL')
db = SQLAlchemy(app)


class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(128), nullable=False)
    last_name = db.Column(db.String(128), nullable=False)
    orders = db.relationship('Order', backref='clients', cascade="all,delete")

    def __init__(self, first_name: str, last_name: str):
        self.first_name = first_name
        self.last_name = last_name

    def serialize(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name
        }


class ClientAccount(db.Model):
    __tablename__ = 'clients_accounts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(128), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey(
        'clients.id'), unique=True, nullable=False)

    def __init__(self, username: str, password: str, client_id: int):
        self.username = username
        self.password = password
        self.client_id = client_id

    def serialize(self):
        return {
            'username': self.username,
            'client_id': self.client_id
        }


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.DateTime,
                     default=datetime.datetime.utcnow,
                     nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey(
        'clients.id'), nullable=False)

    def __init__(self, client_id: int):
        self.client_id = client_id

    def serialize(self):
        return {
            'id': self.id,
            'date': self.date,
            'client_id': self.client_id
        }


orders_medicines = db.Table(
    'orders_medicines',
    db.Column(
        'order_id', db.Integer,
        db.ForeignKey('orders.id'),
        primary_key=True
    ),

    db.Column(
        'medicine_id', db.Integer,
        db.ForeignKey('medicines.id'),
        primary_key=True
    )
)


class Laboratory(db.Model):
    __tablename__ = 'laboratories'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    location = db.Column(db.String(128), nullable=True)

    def __init__(self, name: str, location: str):
        self.name = name
        self.location = location

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location
        }


class Medicine(db.Model):
    __tablename__ = 'medicines'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(128), nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    recommendations = db.Column(db.String(280), nullable=True)
    laboratory_id = db.Column(db.Integer, db.ForeignKey(
        'laboratories.id'), nullable=False)
    medicines_in_orders = db.relationship(
        'Order', secondary=orders_medicines,
        lazy='subquery',
        backref=db.backref('orderes_medicines', lazy=True)
    )

    def __init__(self, name: str, due_date: datetime, recommendations: str, laboratory_id: int):
        self.name = name
        self.due_date = due_date
        self.recommendations = recommendations
        self.laboratory_id = laboratory_id

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'due_date': self.due_date,
            'recommendations': self.recommendations
        }


db.create_all()


@app.route('/clients/all', methods=['GET'])
def clientsindex():
    clients = Client.query.all()
    result = []
    for c in clients:
        result.append(c.serialize())
    return jsonify(result)


@app.route('/clients/<int:id>', methods=['GET'])
def clientsshow(id: int):
    c = Client.query.get_or_404(id)
    return jsonify(c.serialize())


@app.route('/clients', methods=['POST'])
def clientscreate():
    if 'first_name' not in request.json or 'last_name' not in request.json:
        return abort(400)
    c = Client(
        first_name=request.json['first_name'],
        last_name=(request.json['last_name'])
    )
    db.session.add(c)
    db.session.commit()
    return jsonify(c.serialize())


@app.route('/clients/<int:id>', methods=['DELETE'])
def clientsdelete(id: int):
    c = Client.query.get_or_404(id)
    try:
        db.session.delete(c)
        db.session.commit()
        return jsonify(True)
    except:
        return jsonify(False)


@app.route('/clients/<int:id>/orders', methods=['GET'])
def orders_made(id: int):
    c = Client.query.get_or_404(id)
    result = []
    for o in c.orders:
        result.append(o.serialize())
    return jsonify(result)


@app.route('/clientsaccounts/all', methods=['GET'])
def caindex():
    clientsaccounts = ClientAccount.query.all()
    result = []
    for ca in clientsaccounts:
        result.append(ca.serialize())
    return jsonify(result)


@app.route('/clientsaccounts/<int:id>', methods=['GET'])
def cashow(id: int):
    ca = ClientAccount.query.get_or_404(id)
    return jsonify(ca.serialize())


@app.route('/clientsaccounts', methods=['POST'])
def cacreate():
    if 'username' not in request.json or 'password' not in request.json or 'client_id' not in request.json:
        return abort(400)
    ca = ClientAccount(
        client_id=request.json['client_id'],
        username=request.json['username'],
        password=request.json['password']
    )
    db.session.add(ca)
    db.session.commit()
    return jsonify(ca.serialize())


@app.route('/clientsaccounts/<int:id>', methods=['DELETE'])
def cadelete(id: int):
    ca = ClientAccount.query.get_or_404(id)
    try:
        db.session.delete(ca)
        db.session.commit()
        return jsonify(True)
    except:
        return jsonify(False)


@app.route('/clientsaccounts/<int:id>', methods=['PATCH', 'PUT'])
def caupdate(id: int):

    ca = ClientAccount.query.get_or_404(id)

    if 'username' not in request.json or 'password' not in request.json:
        return abort(400)

    if 'username' in request.json:
        if len(request.json['username']) < 1:
            return abort(400)
        ca.username = request.json['username']
    if 'password' in request.json:
        if len(request.json['password']) < 5:
            return abort(400)
        ca.password = request.json['password']

    try:
        db.session.commit()
        return jsonify(ca.serialize())
    except:
        return jsonify(False)


@app.route('/laboratories/all', methods=['GET'])
def labindex():
    lab = Laboratory.query.all()
    result = []
    for l in lab:
        result.append(l.serialize())
    return jsonify(result)


@app.route('/laboratories/<int:id>', methods=['GET'])
def labshow(id: int):
    lab = Laboratory.query.get_or_404(id)
    return jsonify(lab.serialize())


@app.route('/laboratories', methods=['POST'])
def labcreate():
    if 'name' not in request.json:
        return abort(400)
    lab = Laboratory(
        name=request.json['name'],
        location=request.json['location'],
    )
    db.session.add(lab)
    db.session.commit()
    return jsonify(lab.serialize())


@app.route('/laboratories/<int:id>', methods=['DELETE'])
def labdelete(id: int):
    lab = Laboratory.query.get_or_404(id)
    try:
        db.session.delete(lab)
        db.session.commit()
        return jsonify(True)
    except:
        return jsonify(False)



@app.route('/medicines/all', methods=['GET'])
def medindex():
    medicines = Medicine.query.all()
    result = []
    for m in medicines:
        result.append(m.serialize())
    return jsonify(result)


@app.route('/medicines/<int:id>', methods=['GET'])
def medshow(id: int):
    medicine = Medicine.query.get_or_404(id)
    return jsonify(medicine.serialize())


@app.route('/medicines', methods=['POST'])
def medcreate():
    if 'name' not in request.json or 'due_date' not in request.json or 'laboratory_id' not in request.json:
        return abort(400)
    m = Medicine(
        name=request.json['name'],
        due_date=(request.json['due_date']),
        recommendations=(request.json['recommendations']),
        laboratory_id=(request.json['laboratory_id'])
    )
    db.session.add(m)
    db.session.commit()
    return jsonify(m.serialize())


@app.route('/medicines/<int:id>', methods=['DELETE'])
def meddelete(id: int):
    m = Medicine.query.get_or_404(id)
    try:
        db.session.delete(m)
        db.session.commit()
        return jsonify(True)
    except:
        return jsonify(False)


@app.route('/medicines/<int:id>', methods=['PATCH', 'PUT'])
def updaterecommendation(id: int):

    m = Medicine.query.get_or_404(id)

    if 'recommendations' not in request.json:
        return abort(400)

    m.recommendations = request.json['recommendations']

    try:
        db.session.commit()
        return jsonify(m.serialize())
    except:
        return jsonify(False)


@app.route('/orders/all', methods=['GET'])
def ordersindex():
    orders = Order.query.all()
    result = []
    for o in orders:
        result.append(o.serialize())
    return jsonify(result)


@app.route('/orders/<int:id>', methods=['GET'])
def ordershow(id: int):
    c = Order.query.get_or_404(id)
    return jsonify(c.serialize())


@app.route('/orders/<int:id>', methods=['DELETE'])
def ordersdelete(id: int):
    o = Order.query.get_or_404(id)
    try:
        db.session.delete(o)
        db.session.commit()
        return jsonify(True)
    except:
        return jsonify(False)


@app.route('/orders', methods=['POST'])
def orderscreate():
    if 'client_id' not in request.json and 'medicine_id' not in request.json:
        return abort(400)

    Client.query.get_or_404(request.json['client_id'])
    Medicine.query.get_or_404(request.json['medicine_id'])

    medicine_id = request.json['medicine_id']

    o = Order(
        client_id=request.json['client_id']
    )

    db.session.add(o)
    db.session.commit()

    try:
        stmt = sqlalchemy.insert(orders_medicines).values(order_id=o.id, medicine_id=medicine_id
                                                          )
        db.session.execute(stmt)
        db.session.commit()
        return jsonify(o.serialize())
    except:
        return jsonify(False)


@app.route('/orders/<int:id>/ordered_medicines', methods=['GET'])
def ordered_medicines(id: int):
    o = Order.query.get_or_404(id)
    result = []
    for m in o.orderes_medicines:
        result.append(m.serialize())
    return jsonify(result)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
