from datetime import datetime
from app import db, login
from flask_login import UserMixin
from hashlib import md5

from werkzeug.security import generate_password_hash, check_password_hash

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    homes = db.relationship('Home', backref='owner', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

class Home(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140))
    url = db.Column(db.String(140))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    devices = db.relationship('Device', backref='home', lazy='dynamic')
    public = db.Column(db.Boolean)

    def __repr__(self):
        return f'<Home {self.name}, owner {self.owner}, public {self.public}, url {self.url}>'

    def is_public(self):
        return self.public

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140))
    home_id = db.Column(db.Integer, db.ForeignKey('home.id'))
    data = db.relationship('DataPoint', backref='device', lazy='dynamic')
    categories = db.relationship('Category', backref='device', lazy='dynamic')

    def __repr__(self):
        return f"<Device {self.name}, home {self.home}>"

    def get_last_value(self):
        return self.data.order_by(DataPoint.timestamp.desc()).first()
        
    def get_all_entries(self):
        return self.data.order_by(DataPoint.timestamp.desc())

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140))
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'))
    lower_bound = db.Column(db.Integer)
    upper_bound = db.Column(db.Integer)
    color = db.Column(db.String(6))
    alert = db.Column(db.Boolean)

    def __repr__(self):
        return f"<Category {self.name}, device {self.device}>"
    
    def check_within_bounds(self, val):
        if self.lower_bound is None or val > self.lower_bound:
            if self.upper_bound is None or val <= self.upper_bound:
                return True
        return False

class DataPoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'))
    value_id = db.Column(db.Integer, default=0)
    datatype = db.Column(db.Integer) #temp is type 0, water type 1
    value = db.Column(db.Float)

    def __repr__(self):
        return f"<DataPoint {self.id}, time {self.timestamp}, value {self.value}, type {self.datatype}, device {self.device}>"

    def format(self):
        # need to fix this, abstract to more types sourced somewhere else
        # for now 0=temp in c is all we're dealing with
        if self.datatype == 0:
            return str(self.value * (9/5) + 32)
