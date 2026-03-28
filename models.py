from datetime import datetime
from extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='customer')  # customer, staff, admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship('DatCho', backref='user', lazy=True)
    reviews = db.relationship('DanhGia', backref='user', lazy=True)
    invoices = db.relationship('HoaDon', backref='user', lazy=True)
    notifications = db.relationship('ThongBao', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class HoCau(db.Model):
    __tablename__ = 'ho_cau'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.String(255))
    district = db.Column(db.String(80))
    area = db.Column(db.Float)
    price_per_hour = db.Column(db.Float)
    status = db.Column(db.String(20), default='open')  # open, closed
    image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    fish_types = db.relationship('LoaiCa', secondary='ho_cau_loai_ca', backref='ho_ca')
    bookings = db.relationship('DatCho', backref='ho_cau', lazy=True)
    activities = db.relationship('HoatDong', backref='ho_cau', lazy=True)
    reviews = db.relationship('DanhGia', backref='ho_cau', lazy=True)


class LoaiCa(db.Model):
    __tablename__ = 'loai_ca'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float)


class HoCauLoaiCa(db.Model):
    __tablename__ = 'ho_cau_loai_ca'
    id = db.Column(db.Integer, primary_key=True)
    ho_cau_id = db.Column(db.Integer, db.ForeignKey('ho_cau.id'))
    loai_ca_id = db.Column(db.Integer, db.ForeignKey('loai_ca.id'))
    quantity = db.Column(db.Integer, default=0)


class DatCho(db.Model):
    __tablename__ = 'dat_cho'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    ho_cau_id = db.Column(db.Integer, db.ForeignKey('ho_cau.id'))
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    num_people = db.Column(db.Integer)
    note = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    activity = db.relationship('HoatDong', backref='booking', uselist=False)
    invoice = db.relationship('HoaDon', backref='booking', uselist=False)


class HoatDong(db.Model):
    __tablename__ = 'hoat_dong'
    id = db.Column(db.Integer, primary_key=True)
    dat_cho_id = db.Column(db.Integer, db.ForeignKey('dat_cho.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    ho_cau_id = db.Column(db.Integer, db.ForeignKey('ho_cau.id'))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    hours = db.Column(db.Float)
    status = db.Column(db.String(20), default='active')  # active, completed


class HoaDon(db.Model):
    __tablename__ = 'hoa_don'
    id = db.Column(db.Integer, primary_key=True)
    dat_cho_id = db.Column(db.Integer, db.ForeignKey('dat_cho.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    total = db.Column(db.Float)
    discount = db.Column(db.Float, default=0.0)
    khuyen_mai_id = db.Column(db.Integer, db.ForeignKey('khuyen_mai.id'), nullable=True)
    payment_method = db.Column(db.String(50))
    status = db.Column(db.String(20), default='unpaid')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class KhuyenMai(db.Model):
    __tablename__ = 'khuyen_mai'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(140))
    description = db.Column(db.Text)
    percent = db.Column(db.Float)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    active = db.Column(db.Boolean, default=True)


class DanhGia(db.Model):
    __tablename__ = 'danh_gia'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    ho_cau_id = db.Column(db.Integer, db.ForeignKey('ho_cau.id'))
    rating = db.Column(db.Integer)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved = db.Column(db.Boolean, default=False)


class ThongBao(db.Model):
    __tablename__ = 'thong_bao'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    title = db.Column(db.String(140))
    message = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

