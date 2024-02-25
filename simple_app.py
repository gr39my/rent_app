from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3

app = Flask(__name__)
app.secret_key = "your_secret_key"  # セッションを安全に管理するためのシークレットキー

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
        # SQLite データベースに接続
        conn = sqlite3.connect('rent_app.sqlite3')
        cur = conn.cursor()
        
        # テーブルからデータを取得
        cur.execute('SELECT * FROM rental_properties')  # 必要に応じてテーブル名を変更してください
        items = cur.fetchall()
        
        # データベース接続をクローズ
        conn.close()
        
        return render_template('home.html', user=session['user'], items=items)
    return redirect(url_for('login'))

# /update_preferences エンドポイント
@app.route('/update_preferences', methods=['POST'])
def update_preferences():
    if request.method == 'POST':
        # POSTリクエストから送られてきたJSONデータを取得
        data = request.json
        property_id = data.get('property_id')  # 行のID
        column_name = data.get('column_name')  # 列の名前
        value = data.get('value')  # チェックされたかどうか

        try:
            # property_preferences テーブルに新しい行を追加
            new_preference = PropertyPreference(
                property_id=property_id,
                column_name=column_name,
                value=value
            )
            db.session.add(new_preference)
            db.session.commit()

            # 成功時のレスポンス
            response = {'message': 'Preferences updated successfully'}
            return jsonify(response), 200
        except Exception as e:
            # エラーが発生した場合はエラーレスポンスを返す
            response = {'error': str(e)}
            return jsonify(response), 500
    else:
        # POSTリクエスト以外の場合はエラーレスポンスを返す
        response = {'error': 'Invalid request method'}
        return jsonify(response), 405



@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
