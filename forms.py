from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FloatField, IntegerField, SelectField, DateField, TimeField
from wtforms.validators import DataRequired, Length, EqualTo, Optional, Email


class LoginForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired()])
    password = PasswordField('Mật khẩu', validators=[DataRequired()])
    submit = SubmitField('Đăng nhập')


class RegisterForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired(), Length(3, 80)])
    email = StringField('Email', validators=[Optional(), Email()])
    password = PasswordField('Mật khẩu', validators=[DataRequired(), Length(6, 128)])
    password2 = PasswordField('Nhập lại mật khẩu', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Đăng ký')


class HoCauForm(FlaskForm):
    name = StringField('Tên hồ', validators=[DataRequired()])
    description = TextAreaField('Mô tả', validators=[Optional()])
    address = StringField('Địa chỉ', validators=[Optional()])
    district = StringField('Quận', validators=[Optional()])
    area = FloatField('Diện tích (m2)', validators=[Optional()])
    price_per_hour = FloatField('Giá theo giờ', validators=[Optional()])
    status = SelectField('Trạng thái', choices=[('open','Mở'),('closed','Đóng')])
    submit = SubmitField('Lưu')


class LoaiCaForm(FlaskForm):
    name = StringField('Tên loại cá', validators=[DataRequired()])
    description = TextAreaField('Mô tả', validators=[Optional()])
    price = FloatField('Giá', validators=[Optional()])
    submit = SubmitField('Lưu')


class BookingForm(FlaskForm):
    date = DateField('Ngày', validators=[DataRequired()])
    start_time = TimeField('Giờ bắt đầu', validators=[DataRequired()])
    end_time = TimeField('Giờ kết thúc', validators=[DataRequired()])
    num_people = IntegerField('Số người', validators=[Optional()])
    note = TextAreaField('Ghi chú', validators=[Optional()])
    submit = SubmitField('Đặt chỗ')


class PromotionForm(FlaskForm):
    code = StringField('Mã khuyến mãi', validators=[DataRequired(), Length(max=50)])
    title = StringField('Tiêu đề', validators=[Optional(), Length(max=140)])
    percent = FloatField('Phần trăm giảm', validators=[DataRequired()])
    start_date = DateField('Ngày bắt đầu', validators=[Optional()])
    end_date = DateField('Ngày kết thúc', validators=[Optional()])
    submit = SubmitField('Lưu')


class InvoiceForm(FlaskForm):
    payment_method = StringField('Phương thức thanh toán', validators=[Optional(), Length(max=50)])
    status = SelectField('Trạng thái', choices=[('unpaid','Chưa thanh toán'), ('paid','Đã thanh toán'), ('refunded','Hoàn tiền')])
    submit = SubmitField('Lưu')


class ReviewForm(FlaskForm):
    rating = SelectField('Đánh giá', choices=[('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], validators=[DataRequired()])
    content = TextAreaField('Nội dung', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Gửi đánh giá')


