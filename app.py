from flask import Flask, render_template, request, redirect, url_for, session, abort

# Flaskアプリケーションの初期化
app = Flask(__name__)

# ★重要★ セッション管理のための秘密鍵を設定
# 本番環境では、外部から推測されにくい、より長い文字列を使用してください
app.secret_key = 'your_very_secret_and_complex_key_12345'

# --- 1. ダミーデータ (データベースの代わり) ---

# ダミーユーザーデータ: {ユーザー名: {パスワード, 系統}}
DUMMY_USERS = {
    "testuser": {"password": "password123", "email": "test@example.com", "styles": []},
    "nk230192": {"password": "my_secure_password", "email": "nk@example.com", "styles": ["モード", "カジュアル"]}
}

# 利用可能な系統タグのリスト
ALL_STYLES = [
    "カジュアル", "きれいめ", "ストリート", "モード",
    "フェミニン", "韓国風", "アメカジ", "トラッド",
    "古着", "スポーティ", "コンサバ", "ナチュラル"
]

# --- 2. ルート定義 ---

# ログイン状態のチェックとリダイレクト
@app.route('/')
def index():
    # 開発中は、ログイン状態にかかわらず直接ホーム画面へリダイレクトします。
    # return redirect(url_for('login')) # 以前のコード
    
    # 開発用の暫定対応として、直接ホーム画面へリダイレクト
    return redirect(url_for('home'))

# ログイン処理
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # 認証チェック（ユーザー名またはパスワードが一致するか）
        if username in DUMMY_USERS and DUMMY_USERS[username]['password'] == password:
            session['logged_in'] = True
            session['username'] = username
            session['user_styles'] = DUMMY_USERS[username]['styles'] # ユーザー固有のスタイルをセッションにロード
            return redirect(url_for('home'))
        else:
            # 実際のアプリケーションでは、ここにエラーメッセージを出す処理が必要です
            print("Login failed: Invalid credentials") 
            return render_template('login.html', error="ユーザー名またはパスワードが間違っています。")

    return render_template('login.html')

# アカウント登録処理 (ダミー)
@app.route('/acount', methods=['GET', 'POST'])
def account_registration():
    if request.method == 'POST':
        # 実際にはここでデータベースに新しいユーザーを登録します
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if username in DUMMY_USERS:
            # エラー処理（ユーザー名が既に存在する）
            return render_template('account.html', error="このユーザー名は既に使用されています。")
        
        if password != confirm_password:
            # エラー処理（パスワード不一致）
            return render_template('account.html', error="確認用パスワードが一致しません。")

        # ダミーデータに追加
        DUMMY_USERS[username] = {"password": password, "email": email, "styles": []}
        
        # 登録後、自動ログイン
        session['logged_in'] = True
        session['username'] = username
        session['user_styles'] = []
        return redirect(url_for('home'))

    return render_template('account.html')


# ログアウト処理
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ホーム画面
@app.route('/home')
def home():
    # ★重要★ 開発中はログインチェックをスキップするため、
    # ログインしていない場合の自動リダイレクトをコメントアウトします。
    # if not session.get('logged_in'):
    #     return redirect(url_for('login'))
    
    # セッションから現在の系統を取得。無ければ空のリスト
    current_styles = session.get('user_styles', [])
    
    return render_template('home.html', current_styles=current_styles)

# 詳細画面 (ダミーの商品情報)
@app.route('/detail')
def detail():
    # ★重要★ 開発中はログインチェックをスキップします。
    # if not session.get('logged_in'):
    #     return redirect(url_for('login'))
    
    # 固定のダミー商品データ
    dummy_item = {
        "name": "ウールブレンド オーバーサイズ コート",
        "price": 25990,
        "category": "アウター / コート",
        "photo_url": "https://via.placeholder.com/200/404040?text=Coat",
        "sites": [
            {"name": "ZOZOTOWN", "url": "#"},
            {"name": "公式オンラインストア", "url": "#"},
        ]
    }
    return render_template('detail.html', item=dummy_item)


# 設定画面：系統の選択と保存
@app.route('/setting', methods=['GET', 'POST'])
def setting():
    # ★重要★ 開発中はログインチェックをスキップします。
    # if not session.get('logged_in'):
    #     return redirect(url_for('login'))

    # POSTリクエスト (設定の保存)
    if request.method == 'POST':
        # フォームから選択されたスタイルをリストで取得
        selected_styles = request.form.getlist('style')
        
        # セッションとダミーユーザーデータに保存
        session['user_styles'] = selected_styles
        username = session.get('username')
        if username and username in DUMMY_USERS:
            DUMMY_USERS[username]['styles'] = selected_styles
        
        # ホーム画面へリダイレクト
        return redirect(url_for('home'))

    # GETリクエスト (画面表示と検索)
    else:
        search_query = request.args.get('search', '').strip()
        
        if search_query:
            # 検索クエリに基づいてスタイルをフィルタリング
            available_styles = [
                style for style in ALL_STYLES if search_query.lower() in style.lower()
            ]
        else:
            # 検索クエリがない場合は全て表示
            available_styles = ALL_STYLES
            
        return render_template(
            'setting.html', 
            available_styles=available_styles, 
            search_query=search_query
        )

# アプリケーションのエントリーポイント
if __name__ == '__main__':
    # 開発サーバーの実行
    app.run(debug=True)