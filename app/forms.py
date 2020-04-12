from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, BooleanField, SubmitField, SelectField, IntegerField
from wtforms import FieldList, FormField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from wtforms_components import ColorField
from app.models import User, Home, Device

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')

class CreateHomeForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    url = StringField('Home ID', validators=[DataRequired()])
    is_public = BooleanField('Make Public?', validators=[DataRequired()])
    submit = SubmitField('Create')

    def __init__(self, current_user, *args, **kwargs):
        super(CreateHomeForm, self).__init__(*args, **kwargs)
        self.current_user = current_user

    def validate_name(self, name):
        home = Home.query.filter_by(owner=self.current_user).filter_by(name=name.data).first()
        if home is not None:
            raise ValidationError("Please call your home something else. You've already used this name.")

    def validate_url(self, url):
        home = Home.query.filter_by(url=url.data).first()
        if home is not None:
            raise ValidationError("Please choose a different URL, this one's taken.")

class CategoryForm(FlaskForm):
    category_name = StringField('Category Name', validators=[DataRequired()])
    color = ColorField()
    min_value = IntegerField('Minimum Value')
    max_value = IntegerField('Maximum Value')
    alert = BooleanField('Alert')

class AddDeviceForm(FlaskForm):
    device_id = StringField('Device ID', validators=[DataRequired()])
    device_name = StringField('Device Name', validators=[DataRequired()])
    home = SelectField("Select Home")
    categories = FieldList(FormField(CategoryForm), min_entries=2)
    submit = SubmitField('Add')

    def validate_device_id(self, device_id):
        device = Device.query.filter_by(id=device_id).first()
        if device is None or device.home is not None:
            raise ValidationError("This device isn't available. Please check your device ID or contact us.")