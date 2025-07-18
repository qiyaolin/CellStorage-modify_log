# In app/auth/routes.py
from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse

from app import db                     # Import db from the app package (app/__init__.py)
from app.auth import bp                # Import bp from the current auth package (app/auth/__init__.py)
from app.forms import LoginForm, UserCreationForm, ResetPasswordForm, UserEditForm
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
        flash(f'User "{user.username}" has been created successfully with role "{user.role}".', 'success')
        return redirect(url_for('auth.list_users'))
    return render_template('auth/create_user.html', title='Create New User', form=form)


@bp.route('/users')
@login_required
@admin_required
def list_users():
    users = User.query.order_by(User.username).all()
    return render_template('auth/list_users.html', title='Users', users=users)


@bp.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserEditForm(original_username=user.username)
    if form.validate_on_submit():
        user.username = form.username.data
        user.role = form.role.data
        db.session.commit()
        flash(f'User "{user.username}" has been updated.', 'success')
        return redirect(url_for('auth.list_users'))
    elif request.method == 'GET':
        form.username.data = user.username
        form.role.data = user.role
    return render_template('auth/edit_user.html', title='Edit User', form=form)


@bp.route('/reset_password', methods=['GET', 'POST'])
@login_required
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        current_user.set_password(form.password.data)
        db.session.commit()
        flash('Password updated.', 'success')
        return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', title='Reset Password', form=form)
