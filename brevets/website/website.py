import random

import flask
import requests
from urllib.parse import urlparse, urljoin
from passlib.apps import custom_app_context as pwd_context
from flask import Flask, request, render_template, redirect, url_for, flash, abort
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user, UserMixin,
                         confirm_login, fresh_login_required)
from flask_wtf import FlaskForm as Form
from wtforms import BooleanField, StringField, validators


class LoginForm(Form):
    username = StringField('Username', [
        validators.Length(min=2, max=25,
                          message=u"Huh, little too short for a username."),
        validators.InputRequired(u"Forget something?")])
    password = StringField('Password', [
        validators.Length(min=2, max=25,
                          message=u"Huh, little too short for a password."),
        validators.InputRequired(u"Forget something?")])
    remember = BooleanField('Remember me')


class RegisterForm(Form):
    username = StringField('Username', [
        validators.Length(min=2, max=25,
                          message=u"Huh, little too short for a username."),
        validators.InputRequired(u"Forget something?")])
    password = StringField('Password', [
        validators.Length(min=2, max=25,
                          message=u"Huh, little too short for a password."),
        validators.InputRequired(u"Forget something?")])


def is_safe_url(target):
    """
    :source: https://github.com/fengsp/flask-snippets/blob/master/security/redirect_back.py
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


class User(UserMixin):
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.token = "Unknown"

    def set_token(self, token):
        self.token = token
        return self


app = Flask(__name__)

app.secret_key = "and the cats in the cradle and the silver spoon"

app.config.from_object(__name__)

login_manager = LoginManager()

login_manager.session_protection = "strong"

login_manager.login_view = "login"
login_manager.login_message = u"Please log in to access this page."

login_manager.refresh_view = "login"
login_manager.needs_refresh_message = (
    u"To protect your account, please re-authenticate to access this page."
)
login_manager.needs_refresh_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


login_manager.init_app(app)


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route("/selectdata")
@login_required
def selectdata():
    return render_template("selectdata.html")


@app.route("/registration", methods=["GET", "POST"])
def registration():
    form = RegisterForm()
    if form.validate_on_submit() and request.method == "POST" and "username" in request.form and "password" in request.form:
        username = request.form["username"]
        password = pwd_context.hash(request.form["password"])
        assert pwd_context.verify(request.form["password"], password)
        r = requests.post('http://restapi:5000/register' + '?u=' + username + '&p=' + password)
        if r:
            flash("Registered!")
            next = request.args.get("next")
            if not is_safe_url(next):
                abort(400)
            return redirect(next or url_for('login'))
        else:
            flash("Sorry, but you could not register.")
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit() and request.method == "POST" and "username" in request.form and "password" in request.form:
        username = request.form["username"]
        password = pwd_context.hash(request.form["password"])
        assert pwd_context.verify(request.form["password"], password)
        token = requests.get('http://restapi:5000/token' + '?u=' + username + '&p=' + password)
        if token:
            app.logger.debug("Got a token!")
            remember = request.form.get("remember", "false") == "true"
            user = User(u"{}".format(random.randint(0, 100)), u"{}".format(username))
            user.set_token(token)
            if login_user(user, remember=remember):
                flash("Logged in!")
                flash("I'll remember you") if remember else None
                next = request.args.get("next")
                if not is_safe_url(next):
                    abort(400)
                return redirect(next or url_for('index'))
            else:
                flash("Sorry, but you could not log in.")
        else:
            flash(u"Invalid username and/or password.")
    return render_template("login.html", form=form)


@app.route('/listdata', methods=["POST"])
def listdata():
    app.logger.debug("Got a form submission")
    if flask.request.form.get('dtype') == '':
        dtype = 'json'
    else:
        dtype = flask.request.form.get('dtype')
    if flask.request.form.get('topk') != '':
        topk = flask.request.form.get('topk')
    else:
        topk = '0'
    which = flask.request.form.get('which')
    app.logger.debug(f"dtype: {dtype}")
    app.logger.debug(f"topk: {topk}")
    app.logger.debug(f"which: {which}")
    r = requests.get('http://restapi:5000/' + which + '/' + dtype + '?top=' + topk + '?token=' + current_user.token)
    return render_template('listdata.html', data=r.text)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.")
    return redirect(url_for("index"))


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
