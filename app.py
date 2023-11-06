from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
import cx_Oracle 


from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

# Config Oracle
# init Oracle
oracle = cx_Oracle.connect(user='sys', password='Hachimi1', dsn='localhost/orcl', mode=cx_Oracle.SYSDBA)



# Index
@app.route('/')
def index():
    return render_template('home.html')


# About
@app.route('/about')
def about():
    return render_template('about.html')


# Articles
@app.route('/articles')
def articles():
    # Create cursor
    cur = oracle.cursor()
    # Get articles

    cur.execute("SELECT is_admin FROM users WHERE username = :username", {'username': session['username']})
    user = cur.fetchone()
    if user and user[0] == 1:
        result = cur.execute("SELECT * FROM articles")
    else:
        result = cur.execute("SELECT * FROM articles WHERE author = :username", {'username': session['username']})

    
    articles = []
    for id, title, author, body, createdate in result.fetchall():
        articles.append({
            "id": id,
            "title": title,
            "author": author,
            "body": body.read(),  # convert the CLOB to a string
            "createdate": createdate
        })

    if len(articles) > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)
    # Close connection
    cur.close()


#Single Article
@app.route('/article/<string:id>/')
def article(id):
    # Create cursor
    cur = oracle.cursor()

    # Get article
    result = cur.execute("SELECT * FROM articles WHERE id = :id", {'id': id})


    article = {}
    for id, title, author, body, createdate in result.fetchall():
        article = {
            "id": id,
            "title": title,
            "author": author,
            "body": body.read(),  # convert the CLOB to a string
            "createdate": createdate
        }

    return render_template('article.html', article=article )


# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')
    secret_key = StringField('Secret Key', [validators.Length(min=1, max=100), validators.Optional()], render_kw={"type": "password"})





# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data)) 
        secret_key = form.secret_key.data
        is_admin = False
        if form.secret_key.data :
            if secret_key == "secrt_key":
                is_admin = True
            else :
                flash('Incorrect secret password', 'danger')
                return render_template('register.html', form=form)
        # Create cursor
        cur = oracle.cursor()
        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password,is_admin) VALUES(:1, :2, :3, :4, :5)", (name, email, username, password,is_admin))
        # Commit to DB
        oracle.commit()
        # Close connection
        cur.close()
        flash('You are now registered and can log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']
        # Create cursor
        cur = oracle.cursor()
        # Get user by username
        cur.execute("SELECT * FROM users WHERE username = :username", {'username': username})
        result = cur.fetchall()
        if len(result) > 0:
            # Get stored hash
            data = result[0]
            password = data[4]
            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username
                flash('You are now logged in', 'success')
                return render_template('dashboard.html')
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)
    return render_template('login.html')


# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = oracle.cursor()

    # Get articles
    cur.execute("SELECT is_admin FROM users WHERE username = :username", {'username': session['username']})
    user = cur.fetchone()
    if user and user[0] == 1:
        result = cur.execute("SELECT * FROM articles")
    else:
        result = cur.execute("SELECT * FROM articles WHERE author = :username", {'username': session['username']})
    articles = []
    for id, title, author, body, createdate in result.fetchall():
        articles.append({
            "id": id,
            "title": title,
            "author": author,
            "body": body.read(),  # convert the CLOB to a string
            "createdate": createdate
        })

    if len(articles) > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()


# Userlist
@app.route('/Userlist')
@is_logged_in
def Userlist():
    # Create cursor
    cur = oracle.cursor()
    # Get users
    

    cur.execute("SELECT is_admin FROM users WHERE username = :username", {'username': session['username']})
    user = cur.fetchone()
    if user and user[0] == 1:
        result = cur.execute("SELECT * FROM USERS")
    else:
        result = cur.execute("SELECT * FROM USERS WHERE username = :username", {'username': session['username']})





    print(result)
    users = []
    for id, name, email, username, password, createdate, is_admin in result.fetchall():
        users.append({
            "id": id,
            "name": name,
            "email": email,
            "username": username,
            "password": password,
            "createdate": createdate,
            "is_admin": is_admin
        })
    if len(users) > 0:
        return render_template('Userlist.html',users=users)
    else:
        msg = 'No Users Found'
    return render_template('Userlist.html', msg=msg)

    # Close connection
    cur.close()


# Article Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

# Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create Cursor
        cur = oracle.cursor()

        # Execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(:1, :2, :3)",(title, body, session['username']))

        # Commit to DB
        oracle.commit()

        #Close connection
        cur.close()

        flash('Article Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)




# Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    cur = oracle.cursor()
    # Get article by id
    cur.execute("SELECT * FROM articles WHERE id = :id", {'id': id})
    result = cur.fetchone()
    if result is None:
        cur.close()
        flash('Article not found', 'danger')
        return redirect(url_for('dashboard'))
    article = {
        "id": result[0],
        "title": result[1],
        "author": result[2],
        "body": result[3].read(),  # convert the CLOB to a string
        "createdate": result[4]
    }
    cur.close()
    # Get form
    form = ArticleForm(request.form)
    # Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']
    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']
        # Create Cursor
        cur = oracle.cursor()
        app.logger.info(title)
        # Execute
        cur.execute("UPDATE articles SET title=:1, body=:2 WHERE id=:3", (title, body, id))
        # Commit to DB
        oracle.commit()
        #Close connection
        cur.close()
        flash('Article Updated', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_article.html', form=form)

# Edit User
@app.route('/edit_user/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_user(id):
    # Create cursor
    cur = oracle.cursor()

    # Get article by id
    cur.execute("SELECT * FROM USERS WHERE id = :id", {'id': id})
    result = cur.fetchone()

    if result is None:
        cur.close()
        flash('User not found', 'danger')
        return redirect(url_for('dashboard'))

    article = {
        "id": result[0],
        "title": result[1],
        "author": result[2],
        "body": result[3].read(),  # convert the CLOB to a string
        "createdate": result[4]
    }

    cur.close()
    # Get form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cur = oracle.cursor()
        app.logger.info(title)
        # Execute
        cur.execute("UPDATE articles SET title=:1, body=:2 WHERE id=:3", (title, body, id))
        # Commit to DB
        oracle.commit()

        #Close connection
        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)


# Delete Article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create cursor
    cur = oracle.cursor()

    # Execute
    cur.execute("DELETE FROM articles WHERE id = :id", {'id': id})

    # Commit to DB
    oracle.commit()

    #Close connection
    cur.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))

# Delete User
@app.route('/delete_user/<string:id>', methods=['POST'])
@is_logged_in
def delete_user(id):
    # Create cursor
    cur = oracle.cursor()

    # Execute
    cur.execute("DELETE FROM USERS WHERE id = :id", {'id': id})

    # Commit to DB
    oracle.commit()

    #Close connection
    cur.close()

    flash('User Deleted', 'success')

    return redirect(url_for('Userlist'))

if __name__ == '__main__':
    app.secret_key='Hachimi1'
    app.run(debug=True)
