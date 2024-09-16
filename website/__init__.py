from flask import *
import sqlite3
import os

current_directory = os.path.dirname(os.path.abspath(__file__))


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = "secret key"


    from .views import views
    app.register_blueprint(views, url_prefix='/')

    connection = sqlite3.connect(current_directory + '\\mainDB.db')
    cur = connection.cursor()

    table_name = 'products'
    # cur.execute(f"DROP TABLE IF EXISTS {table_name};")
    # cur.execute(f"""
    # DELETE FROM {table_name}
    # WHERE product_price=0;
    # """)
    # connection.commit()
    query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';"
    listOfTables = cur.execute(query).fetchall()

    if listOfTables == []:
        create_table_query = f"""
        CREATE TABLE {table_name} (
            id INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL,
            product_price REAL NOT NULL,
            stock INTEGER NOT NULL,
            image TEXT NOT NULL,
            description TEXT
        );
        """
        cur.execute(create_table_query)
        connection.commit()

    connection.close()


    return app


# print("Created Database!")
