from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, SelectField
from passlib.hash import sha256_crypt
from functools import wraps

#creating an app instance
app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_PORT'] = 3308
app.config['MYSQL_DB'] = 'stocks'
#we want results from the database to be returned as dictionary, by default its a tuple
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init MYSQL
mysql = MySQL(app)

#Index
@app.route('/')
def index():
    return render_template('home.html')

#Products
@app.route('/products')
def products():
    #create cursor
    cur=mysql.connection.cursor()

    #Get products
    result = cur.execute("SELECT * FROM products")

    products = cur.fetchall()

    if result>0:
        return render_template('products.html', products = products)
    else:
        msg='No products found'
        return render_template('products.html', msg=msg)
    #close connection
    cur.close()

#Locations
@app.route('/locations')
def locations():
    #create cursor
    cur=mysql.connection.cursor()

    #Get locations
    result = cur.execute("SELECT * FROM locations")

    locations = cur.fetchall()

    if result>0:
        return render_template('locations.html', locations = locations)
    else:
        msg='No locations found'
        return render_template('locations.html', msg=msg)
    #close connection
    cur.close()

#Product Movements
@app.route('/product_movements')
def product_movements():
    #create cursor
    cur=mysql.connection.cursor()

    #Get products
    result = cur.execute("SELECT * FROM productmovements")

    movements = cur.fetchall()

    if result>0:
        return render_template('product_movements.html', movements = movements)
    else:
        msg='No product movements found'
        return render_template('product_movements.html', msg=msg)
    #close connection
    cur.close()

#Single Article
@app.route('/article/<string:id>/')
def article(id):
    #create cursor
    cur=mysql.connection.cursor()

    #Get article
    result = cur.execute("SELECT * FROM articles WHERE id = %s",[id])

    article = cur.fetchone()
    return render_template('article.html', article = article)

#Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=1, max=25)])
    email = StringField('Email', [validators.length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

#user register
@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute Query
        cur.execute("INSERT into users(name, email, username, password) VALUES(%s,%s,%s,%s)",(name, email, username, password))

        #Commit to DB
        mysql.connection.commit()

        #close connection
        cur.close()

        #for flash messages taking parameter and the category of message to be flashed
        flash("You are now registered and can log in", "success")
        
        #when registration is successful redirect to home
        return redirect(url_for('login'))
    return render_template('register.html', form = form)

#User login
@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        #Get form fields
        username = request.form['username']
        password_candidate = request.form['password']

        #create cursor
        cur = mysql.connection.cursor()

        #get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            #Get the stored hash
            data = cur.fetchone()
            password = data['password']

            #compare passwords
            if sha256_crypt.verify(password_candidate, password):
                #Passed
                session['logged_in'] = True
                session['username'] = username

                flash("you are now logged in","success")
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid Login'
                return render_template('login.html', error=error)
            #Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)
    return render_template('login.html')

#check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login','danger')
            return redirect(url_for('login'))
    return wrap

#Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash("You are now logged out", "success")
    return redirect(url_for('login'))

#Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    #create cursor
    cur=mysql.connection.cursor()

    #Get products
    result = cur.execute("SELECT product_id, to_location, qty FROM productmovements")

    products = cur.fetchall()
    #Get 
    result = cur.execute("SELECT * FROM locations")
    locations = cur.fetchall()

    if result>0:
        return render_template('dashboard.html', products = products)
    else:
        msg='No products found'
        return render_template('dashboard.html', msg=msg)
    #close connection
    cur.close()

#Product Form Class
class ProductForm(Form):
    product_id = StringField('Product ID', [validators.Length(min=1, max=200)])

#Add Product
@app.route('/add_product', methods=['GET', 'POST'])
@is_logged_in
def add_product():
    form = ProductForm(request.form)
    if request.method == 'POST' and form.validate():
        product_id = form.product_id.data

        #create cursor
        cur = mysql.connection.cursor()

        #execute
        cur.execute("INSERT into products VALUES(%s)",(product_id,))

        #commit to DB
        mysql.connection.commit()

        #close connection
        cur.close()

        flash("Product Added", "success")

        return redirect(url_for('products'))

    return render_template('add_product.html', form=form)

#Edit Product
@app.route('/edit_product/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_product(id):
    #Create cursor
    cur = mysql.connection.cursor()

    #Get article by id
    result = cur.execute("SELECT * FROM products where product_id = %s", [id])

    product = cur.fetchone()

    #Get form
    form = ProductForm(request.form)

    #populate product form fields
    form.product_id.data = product['product_id']

    if request.method == 'POST' and form.validate():
        product_id = request.form['product_id']
        #create cursor
        cur = mysql.connection.cursor()

        #execute
        cur.execute("UPDATE products SET product_id=%s WHERE product_id=%s",(product_id, id))

        #commit to DB
        mysql.connection.commit()

        #close connection
        cur.close()

        flash("Product Updated", "success")

        return redirect(url_for('products'))

    return render_template('edit_product.html', form=form)

#Delete Product
@app.route('/delete_product/<string:id>', methods=['POST'])
@is_logged_in
def delete_product(id):
    #create cursor
    cur = mysql.connection.cursor()

    #execute
    cur.execute("DELETE FROM products WHERE product_id=%s", [id])

    #commit to DB
    mysql.connection.commit()

    #close connection
    cur.close()

    flash("Product Deleted", "success")

    return redirect(url_for('products'))

#Location Form Class
class LocationForm(Form):
    location_id = StringField('Location ID', [validators.Length(min=1, max=200)])

#Add Location
@app.route('/add_location', methods=['GET', 'POST'])
@is_logged_in
def add_location():
    form = LocationForm(request.form)
    if request.method == 'POST' and form.validate():
        location_id = form.location_id.data

        #create cursor
        cur = mysql.connection.cursor()

        #execute
        cur.execute("INSERT into locations VALUES(%s)",(location_id,))

        #commit to DB
        mysql.connection.commit()

        #close connection
        cur.close()

        flash("Location Added", "success")

        return redirect(url_for('locations'))

    return render_template('add_location.html', form=form)

#Edit Location
@app.route('/edit_location/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_location(id):
    #Create cursor
    cur = mysql.connection.cursor()

    #Get article by id
    result = cur.execute("SELECT * FROM locations where location_id = %s", [id])

    location = cur.fetchone()

    #Get form
    form = LocationForm(request.form)

    #populate article form fields
    form.location_id.data = location['location_id']

    if request.method == 'POST' and form.validate():
        location_id = request.form['location_id']
        #create cursor
        cur = mysql.connection.cursor()

        #execute
        cur.execute("UPDATE locations SET location_id=%s WHERE location_id=%s",(location_id, id))

        #commit to DB
        mysql.connection.commit()

        #close connection
        cur.close()

        flash("Location Updated", "success")

        return redirect(url_for('locations'))

    return render_template('edit_location.html', form=form)

#Delete Location
@app.route('/delete_location/<string:id>', methods=['POST'])
@is_logged_in
def delete_location(id):
    #create cursor
    cur = mysql.connection.cursor()

    #execute
    cur.execute("DELETE FROM locations WHERE location_id=%s", [id])

    #commit to DB
    mysql.connection.commit()

    #close connection
    cur.close()

    flash("Location Deleted", "success")

    return redirect(url_for('locations'))


#Product Movement Form Class
class ProductMovementForm(Form):
    from_location = StringField('From Location')
    to_location = StringField('To Location')
    product_id = StringField('Product ID')
    qty = StringField('Quantity')

#Add Product Movement
@app.route('/add_product_movements', methods=['GET', 'POST'])
@is_logged_in
def add_product_movements():
    form = ProductMovementForm(request.form) 
    if request.method == 'POST' and form.validate():
        from_location = form.from_location.data
        to_location = form.to_location.data
        product_id = form.product_id.data 
        qty = form.qty.data
        #Create cursor
        cur = mysql.connection.cursor() 
        #execute
        cur.execute("INSERT into productmovements(from_location, to_location, product_id, qty) VALUES(%s, %s, %s, %s)",(from_location, to_location, product_id, qty))

        #commit to DB
        mysql.connection.commit()

        #close connection
        cur.close()

        flash("Product Movement Added", "success")

        return redirect(url_for('product_movements'))

    return render_template('add_product_movements.html', form=form)

#Edit Product Movement
@app.route('/edit_product_movement/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_product_movements(id):
    #Create cursor
    cur = mysql.connection.cursor()

    #Get article by id
    result = cur.execute("SELECT * FROM productmovements where movement_id = %s", [id])

    movement = cur.fetchone()

    #Get form
    form = ProductMovementForm(request.form)

    #populate article form fields
    form.from_location.data = movement['from_location']
    form.to_location.data = movement['to_location']
    form.product_id.data = movement['product_id']
    form.qty.data = movement['qty']

    if request.method == 'POST' and form.validate():
        from_location = request.form['from_location']
        to_location = request.form['to_location']
        product_id = request.form['product_id']
        qty = request.form['qty']
        #create cursor
        cur = mysql.connection.cursor()

        #execute
        cur.execute("UPDATE productmovements SET from_location=%s, to_location=%s, product_id=%s, qty=%s WHERE movement_id=%s",(from_location, to_location, product_id, qty, id))

        #commit to DB
        mysql.connection.commit()

        #close connection
        cur.close()

        flash("Product Movement Updated", "success")

        return redirect(url_for('product_movements'))

    return render_template('edit_product_movements.html', form=form)

#Delete Product Movements
@app.route('/delete_product_movements/<string:id>', methods=['POST'])
@is_logged_in
def delete_product_movements(id):
    #create cursor
    cur = mysql.connection.cursor()

    #execute
    cur.execute("DELETE FROM productmovements WHERE movement_id=%s", [id])

    #commit to DB
    mysql.connection.commit()

    #close connection
    cur.close()

    flash("Product Movement Deleted", "success")

    return redirect(url_for('product_movements'))

if __name__ == '__main__':
    app.secret_key = "secret123"
    #when the debug mode is on, we do not need to restart the server again and again
    app.run(debug=True)
