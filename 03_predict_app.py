from flask import Flask, render_template
import psycopg2

import configparser

config = configparser.ConfigParser()
config.read('config.ini')

db_user = config['database']['user']
db_password = config['database']['password']
db_host = config['database']['host']
db_name = config['database']['name']
db_port = config['database']['port']


app = Flask(__name__)

conn = psycopg2.connect(
    host=db_host,  # 'localhost' などのホスト名
    dbname=db_name,  # データベース名
    user=db_user,  # ユーザー名
    password=db_password,  # パスワード
    port=db_port  # ポート番号（PostgreSQLのデフォルトポートは5432）
)


@app.route('/')
def home():
    cur = conn.cursor()
    cur.execute('SELECT * FROM rental_properties;')  # 例: 'SELECT * FROM mytable;'
    items = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', items=items)

if __name__ == '__main__':
    app.run(debug=True)
