import os
from flask.ext.bootstrap import Bootstrap
from flask import Flask,render_template, request, session, redirect, url_for,flash
from flask.ext.wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import Required
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Shell
from config import config
from flask.ext.mail import Mail
import random
from bs4 import BeautifulSoup
import requests
import csv
from stop_words import stops
#from models import Result,Role,User


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
mail = Mail(app)

app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] =\
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

db = SQLAlchemy(app)

class NameForm(Form):
    name = StringField('What is your name?', validators=[Required()])
    submit = SubmitField('Submit')

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role')
    def __repr__(self):
        return '<Role %r>' % self.name

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    #gold=db.Column(db.Integer, default=100000)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    def __repr__(self):
        return '<User %r>' % self.username

class Result(db.Model):
    __tablename__ = 'results'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String())
    result_all = db.Column(db.String())
    result_no_stop_words = db.Column(db.String())

    def __init__(self, url, result_all, result_no_stop_words):
        self.url = url
        self.result_all = result_all
        self.result_no_stop_words = result_no_stop_words

    def __repr__(self):
        return '<id {}>'.format(self.id)

#app.config.from_object(os.environ['APP_SETTINGS'])


'''
app.config['SQLALCHEMY_DATABASE_URI'] =\
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')'''


"""def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)
manager.add_command("shell", Shell(make_context=make_shell_context))

migrate = Migrate(app, db)
manager.add_command"""

bootstrap = Bootstrap(app)
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            session['known'] = False
        else:
            session['known'] = True
        session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('index'))
    return render_template('index.html',
        form=form, name=session.get('name'),
        known=session.get('known', False))

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/about/')
def about():
    return render_template("about.html")

@app.route('/testp/')
def testp():
    mydict={'z':10,'p':12}
    mylist=[1,3,4,65,3,23]

    return render_template("testp.html",mydict=mydict,mylist=mylist,stops=stops)

@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
#######################################################################################################################
@app.route('/guesn/',methods=['get','post'])
def count():
    message = None
    error = None
    session['guess_count'] = 0
    session['number']= random.randint(1,100)
    return render_template('guesn.html', message = message)

@app.route('/guess', methods=['post'])
def guess():
    try:
        val = int(request.form['guess'])
    except ValueError:
        error = "That's not an integer! Enter an integer between 1 and 100."
        return render_template('guesn.html', error = error)
    session['guess_count'] += 1
    if int(request.form['guess']) > session['number']:
        message = 'Too high. Enter a smaller number. Your guess count so far is '
        return render_template('guesn.html', message = message)
    elif int(request.form['guess']) < session['number']:
        message = 'Too low. Enter a larger number. Your guess count so far is '
        return render_template('guesn.html', message = message)
    elif int(request.form['guess']) == session['number']:
        message = 'Correct! Congratulations! Your total guesses was '
        return render_template('guesn.html', message = message)

@app.route('/reset', methods=['post'])
def reset():
    message = None
    error = None
    session['guess_count'] = 0
    session['number'] = random.randint(1,100)
    return render_template('guesn.html', message = message)
##########################################################################
@app.route('/scr', methods=['GET', 'POST'])
@app.route('/scraper/', methods=['GET', 'POST'])
def scraper():
    if request.method == 'GET':
        return render_template('links_main.html')
    else:
        links = []
        site = request.form['myUrl']
        r = requests.get("http://" + site)
        data = r.text
        soup = BeautifulSoup(data, "html.parser")
        for link in soup.find_all('a'):
            if 'href' in link.attrs:
                links.append(link)
        return render_template('links.html', site=site, links=links)


