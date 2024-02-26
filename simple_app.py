import logging
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from contextlib import closing

app = Flask(__name__)
app.secret_key = "your_secret_key"  # セッションを安全に管理するためのシークレットキー

# 許可されたカラム名のリストを定義
ALLOWED_COLUMNS = ['want_rent', 'want_rent_if_5000_cheaper', 'want_rent_if_10000_cheaper']

# ログ設定
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# SQLite データベースに接続
conn = sqlite3.connect('rent_app.sqlite3')
conn.execute("PRAGMA foreign_keys = ON")

print("Opened database successfully")

# テーブルを作成
conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)')
print("Table created successfully")
conn.close()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.pop('user', None)  # セッションのユーザーを一旦クリア
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('rent_app.sqlite3')
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cur.fetchone()
        conn.close()
        if user:
            session['user'] = user[0]  # ユーザー名をセッションに格納
            return redirect(url_for('home'))
        else:
            return 'Invalid username/password. Please try again.'
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('rent_app.sqlite3')
        cur = conn.cursor()
        cur.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/home')
def home():
    if 'user' in session:
        # データ読み込み
        conn = sqlite3.connect('rent_app.sqlite3') # SQLite データベースに接続
        cur = conn.cursor()
        cur.execute('SELECT * FROM rental_properties')  # テーブルからデータを取得
        items = cur.fetchall()
        conn.close() # データベース接続をクローズ
        
        # TODO: ユーザーの好みに基づいて、チェック状態を復元するロジックをここに追加する必要があります
        
        return render_template('home.html', user=session['user'], items=items)
    return redirect(url_for('login'))

@app.route('/update_preferences', methods=['POST'])
def update_preferences():
    logging.debug('update_preferences called')
    try:
        # セッションから安全に username を取得
        username = session.get('user')
        property_id = request.json.get('property_id')
        column_name = request.json.get('column_name')
        value = request.json.get('value') in ['true', 'True', 1, '1']

        # column_name の検証
        if column_name not in ALLOWED_COLUMNS:
            logging.debug(f'Invalid column name: {column_name}')
            return jsonify({'error': 'Invalid column name'}), 400

        # データベースに接続
        conn = sqlite3.connect('rent_app.sqlite3')
        cur = conn.cursor()

        # ユーザーと物件の組み合わせで既存のレコードを検索し、存在するかチェック
        cur.execute('SELECT id FROM property_preferences WHERE username = ? AND property_id = ?', (username, property_id))
        if cur.fetchone():
            # 既存のレコードを更新
            cur.execute(f'UPDATE property_preferences SET {column_name} = ? WHERE username = ? AND property_id = ?', (value, username, property_id))
        else:
            # 新しいレコードを挿入
            cur.execute(f'INSERT INTO property_preferences (username, property_id, {column_name}) VALUES (?, ?, ?)', (username, property_id, value))

        conn.commit()  # 変更をコミット
    except Exception as e:
        conn.rollback()  # エラーが発生した場合はロールバック
        logging.error(f'Error: {e}')
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()  # データベース接続を閉じる

    return jsonify({'message': 'Preferences updated successfully'}), 200




@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
