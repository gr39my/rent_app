from flask import Flask, render_template, abort, request, redirect, url_for, flash, current_app
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from urllib.parse import urlparse, urljoin 

app = Flask(__name__)
# 安全なランダム値を使用して秘密鍵を生成
app.secret_key = secrets.token_hex(16)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

    @staticmethod
    def get(user_id):
        db_path = 'rent_app.sqlite3'
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user:
            return User(user['id'], user['username'])
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# ユーザー登録ページ
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = generate_password_hash(password)
        
        # データベースへの接続を開く
        db_path = 'rent_app.sqlite3'
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # 新しいユーザーをデータベースに追加
        cur.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        conn.commit()
        
        # データベース接続を閉じる
        cur.close()
        conn.close()
        
        flash('User registered successfully!')
        return redirect(url_for('login'))
    
    return render_template('register.html')

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        current_app.logger.info(f"Login attempt for user: {username}")
        db_path = 'rent_app.sqlite3'
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            user_obj = User(user['id'], user['username'])
            login_user(user_obj)

            next_page = request.args.get('next')
            # 安全なリダイレクト先を確認
            if not is_safe_url(next_page):
                return abort(400)
            return redirect(next_page or url_for('home'))
        flash('username, passwordの片方または両方に誤りがあります。')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/')
@login_required
def home():
    # SQLiteデータベースファイルへのパス
    db_path = 'rent_app.sqlite3'
    
    # SQLiteデータベースに接続
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # SQLクエリ実行
    cur.execute('SELECT * FROM rental_properties;')
    items = cur.fetchall()
    
    # データベース接続を閉じる
    cur.close()
    conn.close()
    
    # データをテンプレートに渡す
    return render_template('index.html', items=items)

if __name__ == '__main__':
    app.run(debug=True)
