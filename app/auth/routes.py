# In app/auth/routes.py
from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse

from app import db                     # Import db from the app package (app/__init__.py)
from app.auth import bp                # Import bp from the current auth package (app/auth/__init__.py)
from app.forms import LoginForm, UserCreationForm
from app.models import User
from app.decorators import admin_required # Import our custom decorator

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index')) # Assumes 'main.index' will be created later
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        flash(f'Welcome back, {user.username}!', 'success')
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index') # Assumes 'main.index'
        return redirect(next_page)
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('pickup_ids', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/create_user', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    form = UserCreationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'User {user.username} created successfully with role {user.role}!', 'success')
        return redirect(url_for('auth.login')) # Or to a user list page if you create one
    return render_template('auth/create_user.html', title='Create New User', form=form)