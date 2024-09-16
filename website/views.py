from flask import Blueprint, render_template, request, session, flash, jsonify
import sqlite3
from os import path, remove, getcwd
import requests

current_directory = path.dirname(path.abspath(__file__))

views = Blueprint("views", __name__)


@views.route("/add_product", methods=['GET', 'POST'])
def add_product():

    filename = ""
    if request.method == "POST":
        if "submit-button" in request.form:
            product_name = request.form.get("product_name")
            product_price = request.form.get("product_price")
            product_stock = request.form.get("product_stock")
            product_info = request.form.get("product_info")
            if product_info == "":
                product_info = "No Description!"
            img_file = request.files['img_file']
            img_link = request.form.get("img_link")
            filename = img_file.filename

            con = sqlite3.connect(current_directory + "\\mainDB.db")
            cur = con.cursor()
            table_name = 'products'

            select_query = f"SELECT * FROM {table_name} WHERE product_name=?;"
            result = cur.execute(select_query,(product_name,)).fetchall()

            if result:
                flash(
                    f'The Product {product_name} Already Exists!', category="error")

            elif len(product_name) < 4:
                flash('Product\'s name must be greater than 3 characters.',
                    category='error')
            elif product_price == "" or float(product_price) <= 0:
                flash('The price must be greater than 0$.', category='error')
            elif filename == "" and img_link == "":
                flash('Product\'s image should not be empty.', category='error')

            elif filename != "" and img_link != "":
                flash(
                    'You can\'t have both link and file for the image, choose only one.', category='error')
                return render_template("add_product.html")
            elif img_link == "" and filename != "":
                filename = product_name + '.' + filename.split('.')[1]
                img_file.save("website\\static\\" + filename)

                insert_query = f"""
                INSERT INTO {table_name} (product_name, product_price, stock, image, description)
                VALUES (?, ?, ?, ?, ?);
                """

                cur.execute(insert_query, (product_name,
                            product_price, product_stock, filename, product_info))
                con.commit()
                flash('Product added successfully!', category='success')
                return render_template('add_product.html')
            elif img_link != "" and filename == "":
                # download the link and save it in the database
                response = requests.get(img_link)

                content_type = response.headers['Content-Type']
                ext = content_type.split('/')[-1]

                filename = f'{product_name}.{ext}'

                if response.status_code == 200:
                    with open('website\\static\\' + filename, 'wb') as f:
                        f.write(response.content)

                    insert_query = f"""
                    INSERT INTO {table_name} (product_name, product_price, stock, image, description)
                    VALUES (?, ?, ?, ?, ?);
                    """

                    cur.execute(insert_query, (product_name,
                                product_price, product_stock, filename, product_info))
                    con.commit()
                    flash('Product added successfully!', category='success')
                    return render_template('add_product.html')

                else:
                    flash(
                        'Image Link is Invalid! Try another link or upload an image file.', category='error')

            con.close()
        elif "delete-button" in request.form:
            product_name = request.form.get("product_name")
            con = sqlite3.connect(current_directory + "\\mainDB.db")
            cur = con.cursor()
            table_name = 'products'

            select_query = f"SELECT * FROM {table_name} WHERE product_name=?;"
            result = cur.execute(select_query,(product_name,)).fetchall()

            if result:
                img = result[0][4]
                print(img)
                file_path = path.join(current_directory, f"static\\{img}")
                remove(file_path)
                cur.execute(f'DELETE FROM {table_name} WHERE product_name=?', (product_name,))
                con.commit()
                cur.close()
                flash(f"The Product {product_name} Has Been Deleted Successfully!", category='success')
            else:
                flash(f"The Product {product_name} Not Found!", category='error')

    return render_template('add_product.html')


@views.route('/', methods=['GET', 'POST'])
def main_page():
    conn_cart = sqlite3.connect(current_directory + "\\cart.db")
    cursor_cart = conn_cart.cursor()
    cursor_cart.execute('DELETE FROM cart')
    conn_cart.commit()
    
    access_key = 'a234318a63a5457167c41b75e7915058'
    base_currency = 'EUR'
    target_currency = 'IRR'
    url = f'http://data.fixer.io/api/latest?access_key={access_key}&base={base_currency}&symbols={target_currency}'
    params = {
         'access_key': access_key,
         'base': base_currency,
         'symbols': target_currency
    }
    response = requests.get(url, params=params)
    response = requests.get(url)
    data = response.json()
    
    exchange_rate = data['rates'][target_currency]
    conn = sqlite3.connect(current_directory + "\\mainDB.db")
    cursor = conn.cursor()
    cursor.execute('ALTER TABLE products DROP COLUMN irr_price')
    
        
    cursor.execute('ALTER TABLE products ADD COLUMN irr_price INTEGER')
    cursor.execute(f'UPDATE products SET irr_price = CAST(product_price * {exchange_rate} AS INTEGER)')
    conn.commit()
    cursor.close()
    conn.close()

    conn = sqlite3.connect(current_directory + "\\mainDB.db")
    table_name = 'products'
    cursor=conn.cursor()
    query=f'SELECT * from {table_name}'
    cursor.execute(query)
    items=cursor.fetchall()
    cursor.close()
    conn.close()


    

    return render_template('main_page.html',items=items)

@views.route('/cart', methods=['POST'])
def cart():
    conn_cart = sqlite3.connect(current_directory + "\\cart.db")
    cursor_cart = conn_cart.cursor()

    item_id = request.form.get('item_id')
    conn = sqlite3.connect(current_directory + "\\mainDB.db")
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE id=?', (item_id,))
    item = cursor.fetchone()

    cursor_cart.execute('SELECT * FROM cart WHERE id=?', (item_id,))
    item_in_cart = cursor_cart.fetchone()

    if not item_in_cart:
        cursor_cart.execute(
            'INSERT INTO cart (name, euro_price, irr_price, image , id, quantity) VALUES (?, ?, ?, ?, ?, ?)',
            ( item[1], f"{item[2]}€", f"{item[6]} IRR", item[4],item[0], 1)
        )
        conn_cart.commit()
        status = "success"
    else:
        status = "fail"

    cursor.close()
    conn.close()
    cursor_cart.close()
    conn_cart.close()

    return jsonify({"status": status})
    

@views.route('/shopping_cart', methods=['GET','POST'])
def shopping_cart():
    con_cart = sqlite3.connect(path.join(current_directory, "cart.db"))
    table_name = 'cart'
    cursor_cart = con_cart.cursor()
    query = f'SELECT * from {table_name}'
    cursor_cart.execute(query)
    items = cursor_cart.fetchall()

    cursor_cart.execute("SELECT COUNT(*) FROM cart")
    result = cursor_cart.fetchone()
    count = result[0]
    cursor_cart.close()
    con_cart.close()

    return render_template('cart.html', items = items)
    

    
