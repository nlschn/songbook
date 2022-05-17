from app import db
from app.auth import bp

from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user
from app.models import User
from werkzeug.urls import url_parse
from datetime import datetime

from app.auth.forms import SignInForm, SignUpForm

@bp.route('/signin', methods = ['GET', 'POST'])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = SignInForm()

    # If the user submits, check login
    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            # If failed, show the page again
            flash('Invalid username or password')
            return redirect(url_for('auth.signin'))

        # In case of success, sing the user in and continue
        login_user(user, remember=form.remember_me.data)

        # If the user was redirected here from a protected page, the query has the "next" attribute which we can use
        # to find out where they want to go after login
        next_page = request.args.get('next')
        # If this attribute does not exist, redirect to a given page
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.profile')

        return redirect(next_page)

    # Render the template if the page is requested with get
    return render_template('auth/signin.html', form = form, centered = True)


@bp.route('/signout')
def signout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = SignUpForm()

    # if successful, redirect so the user can sign in
    if form.validate_on_submit():
        user = User(username = form.username.data, email = form.email.data, registered = datetime.now)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('auth.signin'))

    # Render the template if the page is requested with get   
    return render_template('auth/signup.html', title='Register', form = form, centered = True)