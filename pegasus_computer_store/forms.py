from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField, FloatField, SelectField, BooleanField, FileField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional, ValidationError
from models import User

class RegistrationForm(FlaskForm):
    username = StringField('用戶名', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('郵箱', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('密碼', validators=[DataRequired(), Length(min=6, max=50)])
    confirm_password = PasswordField('確認密碼', validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('名', validators=[Length(max=50)])
    last_name = StringField('姓', validators=[Length(max=50)])
    phone = StringField('電話', validators=[Length(max=20)])
    submit = SubmitField('注冊')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('用戶名已存在')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('郵箱已被注冊')

class LoginForm(FlaskForm):
    username = StringField('用戶名/郵箱', validators=[DataRequired()])
    password = PasswordField('密碼', validators=[DataRequired()])
    submit = SubmitField('登錄')

class ProductForm(FlaskForm):
    name = StringField('商品名稱', validators=[DataRequired(), Length(max=200)])
    slug = StringField('URL標識', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('詳細描述')
    short_description = StringField('簡短描述', validators=[Length(max=500)])
    price = FloatField('售價', validators=[DataRequired(), NumberRange(min=0)])
    original_price = FloatField('原價', validators=[Optional(), NumberRange(min=0)])
    stock = IntegerField('庫存', validators=[DataRequired(), NumberRange(min=0)])
    sku = StringField('SKU', validators=[Length(max=50)])
    brand = StringField('品牌', validators=[Length(max=100)])
    specifications = TextAreaField('規格參數(JSON格式)')
    category_id = SelectField('分類', coerce=int, validators=[DataRequired()])
    is_featured = BooleanField('設為推薦')
    is_new = BooleanField('設為新品')
    is_active = BooleanField('上架')
    image = FileField('商品圖片')
    submit = SubmitField('保存')

class CartUpdateForm(FlaskForm):
    quantity = IntegerField('數量', validators=[DataRequired(), NumberRange(min=1, max=99)])
    submit = SubmitField('更新')

class CheckoutForm(FlaskForm):
    shipping_name = StringField('收貨人姓名', validators=[DataRequired(), Length(max=100)])
    shipping_phone = StringField('聯系電話', validators=[DataRequired(), Length(max=20)])
    shipping_address = TextAreaField('收貨地址', validators=[DataRequired(), Length(max=300)])
    note = TextAreaField('訂單備注')
    submit = SubmitField('提交訂單')

class ProfileForm(FlaskForm):
    first_name = StringField('名', validators=[Length(max=50)])
    last_name = StringField('姓', validators=[Length(max=50)])
    phone = StringField('電話', validators=[Length(max=20)])
    address = TextAreaField('地址', validators=[Length(max=200)])
    submit = SubmitField('更新資料')