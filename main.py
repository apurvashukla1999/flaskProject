import datetime
import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, DateField, IntegerRangeField, IntegerField, SelectField, \
    SubmitField, TimeField
from wtforms import DecimalField, RadioField, DateTimeField
import MySQLdb.cursors
import hashlib
from flask import Flask, render_template, request, session, redirect, url_for
from flask_mysqldb import MySQL
from wtforms.validators import InputRequired

app = Flask(__name__)

app.secret_key = 'secretkey'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'pythonlogin'

mysql = MySQL(app)


class TimesheetForm(FlaskForm):
    date = DateField("Start time", validators=[InputRequired()], format="%d%b%Y %H:%M")
    startHour = TimeField('Start Time', format='%H:%M', validators=[InputRequired()])
    endHour = TimeField('End Time', format='%H:%M', validators=[InputRequired()])
    role = SelectField('Role', validators=[InputRequired()], choices=[('employee', 'Employee'), ('manager', 'Manager'), ('admin', 'Admin')])
    client = SelectField('ClientID')
    submit = SubmitField()


@app.route("/login", methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        app.logger.info(request.form)
        username = request.form['username']
        password = request.form['password']
        salted_password = password + app.secret_key
        hashed_password = hashlib.sha1(salted_password.encode())
        password = hashed_password.hexdigest()

        # MySQL check
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM accounts WHERE username=%s AND password = %s", (username, password,))
        account = cursor.fetchone()
        # if account exists then
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # redirect to home page
            return redirect(url_for('home'))
        else:
            msg = 'Incorrect username or password.'
    return render_template('index.html', msg=msg)


@app.route("/login/logout")
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route("/login/register", methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # variables for request forms
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        # mysql account check
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username=%s', (username,))
        account = cursor.fetchone()
        # validation check for existing account
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = "Please fill out the form!"
        else:
            salted_password = password + app.secret_key
            hashed_password = hashlib.sha1(salted_password.encode())
            password = hashed_password.hexdigest()
            # form data valid, create mysql statement
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email,))
            mysql.connection.commit()
            msg = "You have successfully registered"

    elif request.method == 'POST':
        msg = 'Please fill the form'  # empty form
    return render_template('register.html', msg=msg)


@app.route("/")
def home():
    if 'loggedin' in session:
        return render_template("home.html", username=session['username'])
    return redirect(url_for('profile'))


@app.route("/sheet", methods=['GET', 'POST'])
def sheet():
    form = TimesheetForm()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT client_name FROM client")
    fetch = cursor.fetchall()
    form.client.choices = [(temp2) for temp2 in fetch]
    if form.validate_on_submit():
        date = form.date.data
        startHour = form.startHour.data
        endHour = form.endHour.data
        role = form.role.data
        client = form.client.data
        submit = form.submit.data
        return '<h1> Hi {}!. Your form is submitted successfully.</h1>'
    return render_template("sheet.html", form=form)


@app.route("/profile")
def profile():
    # Check if the user is logged in
    if 'loggedin' in session:
        # We need all the account info for the user,so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not logged in redirect to login page
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
