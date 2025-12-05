from flask import Flask, render_template, request, redirect, url_for, session
import os 

app = Flask(__name__)

# ★★★ 必須: セッション暗号化のための秘密鍵を設定 ★★★
# このキーがないとセッション（ログイン状態や設定データの一時保存）は動作しません。
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_very_secret_key_default')

# =========================================================
# ルーティング設定
# =========================================================

# 1. '/' ルート: メイン機能画面 (ホーム)
@app.route('/')
def home():
    # セッションからユーザーが選択した系統データを取得
    current_styles = session.get('user_styles', [])
    
    # テンプレートにデータを渡す
    return render_template('home.html', current_styles=current_styles) 
    
# 2. '/login' ルート: ログイン画面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 認証処理は省略。成功と仮定し、ホームへリダイレクト
        return redirect(url_for('home')) 
        
    return render_template('login.html')

# 3. '/acount' ルート: アカウント登録画面
@app.route('/acount', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        # 登録処理は省略。成功と仮定し、ホームへリダイレクト 
        return redirect(url_for('home')) 
        
    return render_template('account.html')

# 4. '/setting' ルート: 設定画面
@app.route('/setting', methods=['GET', 'POST'])
def setting():
    # 系統の全リスト
    all_styles = [
        'フォーマル', 'ストリート', 'カジュアル', 'ヴィンテージ', 'モード', 
        'ユーティリティ', 'アメカジ', 'きれいめ', 'トラッド', 'ロック', 
        '韓国風', 'ノームコア', 'アスレジャー', 'ミリタリー'
    ]
    
    # GETパラメータから検索キーワードを取得
    search_query = request.args.get('search', '').strip()
    available_styles = all_styles
    
    # 検索ロジック: 検索キーワードがあれば絞り込みを行う
    if search_query:
        available_styles = [
            style for style in all_styles
            if search_query.lower() in style.lower()
        ]

    # POSTリクエスト（「設定を保存」ボタン押下時）
    if request.method == 'POST':
        # フォームデータから選択された系統を取得
        selected_styles = request.form.getlist('style')
        
        # ★★★ セッションにデータを保存 ★★★
        session['user_styles'] = selected_styles
        
        # 保存完了後、ホーム画面へリダイレクト
        return redirect(url_for('home')) 
        
    # GETリクエストまたは検索結果の表示
    return render_template('setting.html', 
                           available_styles=available_styles, 
                           search_query=search_query)

# 5. '/detail' ルート: 詳細画面
@app.route('/detail')
def detail():
    # ★★★ 詳細画面表示用のダミーデータ ★★★
    dummy_item_data = {
        'name': 'オーバーサイズ ブレザー',
        'price': 12900,
        'category': 'アウター / ジャケット',
        'photo_url': 'https://via.placeholder.com/150/A0A0A0?Text=BLAZER',
        'sites': [
            {'name': 'ZOZO TOWN', 'url': '#'},
            {'name': 'GU 公式オンラインストア', 'url': '#'},
            {'name': 'Amazon Fashion', 'url': '#'}
        ]
    }
    
    # テンプレートにデータを渡す
    return render_template('detail.html', item=dummy_item_data)

# =========================================================

if __name__ == '__main__':
    # サーバー起動コマンド
    app.run(debug=True, host='0.0.0.0')