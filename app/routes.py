from flask import render_template, flash, redirect, url_for, request, abort
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from datetime import datetime
from app import app, db
from app.forms import LoginForm, RegistrationForm
from app.forms import ResetPasswordRequestForm, ResetPasswordForm, CreateHomeForm, AddDeviceForm
from app.email import send_password_reset_email
from app.models import User, Home, Device, DataPoint

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    return render_template('index.html', title='Home')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

@login_required
@app.route('/create_home', methods=['GET', 'POST'])
def create_home():
    form = CreateHomeForm(current_user=current_user)
    form.is_public.data = True
    if form.validate_on_submit():
        home = Home(owner=current_user, name=form.name.data, public=form.is_public.data, url=form.url)
        db.session.add(home)
        db.session.commit()
        flash('Your home has been added')
        return redirect(url_for('dashboard'))
    return render_template('create_home.html', title='Create a Home', form=form)

@login_required
@app.route('/add_device', methods=['GET', 'POST'])
def add_device():
    form = AddDeviceForm()
    form.home.choices = [(h.id, h.name) for h in Home.query.filter_by(owner=current_user)]
    if form.validate_on_submit():
        home = Home.query.filter_by(owner=current_user).filter_by(id=form.home.data).first()
        device = Device.query.filter_by(id=form.device_id).first()
        device.name = form.device_name.data
        device.home = home
        # go through each category and add those here too. Too much work for now.
        db.session.commit()
        flash('Your device has been added')
        return redirect(url_for('dashboard'))
    return render_template('add_device.html', title='Add a Device', form=form)

@app.route('/upload/<device_id>', methods=['POST'])
def upload_datapoint(device_id):
    device = Device.query.filter_by(id=device_id).first()
    value = request.args.get('value')
    datatype = request.args.get('datatype')
    dp = DataPoint(device=device, value=value, datatype=datatype)
    db.session.add(dp)
    db.session.commit()
    return f"data point {dp} added. thanks" 

@app.route('/dashboard')
@login_required
def dashboard():
    homes = current_user.homes
    return render_template('dashboard.html', user=current_user, homes=homes)

@app.route('/home/<home_url>')
@login_required
def home(home_url):
    current_home = Home.query.filter_by(url=home_url).first_or_404()
    if not current_home.is_public() and current_home.owner != current_user:
        abort(401)
    devices = current_home.devices
    return render_template('view_home.html', user=current_user, current_home=current_home, devices=devices)

@app.route('/device/<device_id>')
@login_required
def device(device_id):
    current_device = Device.query.filter_by(id=device_id).first()


    entries = [val for val in current_device.get_all_entries()]
    values = [val.format() for val in entries]

    labels = [val.timestamp for val in entries]

    if not current_device.home.is_public() and current_device.home.owner != current_user:
        abort(401)
    return render_template(
        'view_device.html', 
        user=current_user, 
        current_device=current_device, 
        title = f"{current_device.name} | {current_device.home.name}", 
        max=17000, 
        labels=labels, 
        values=values
    )