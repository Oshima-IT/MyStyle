# システム動作手順書（MyStyle トレンドアプリ）

## 1. 前提条件
- Python 3.12 以上がインストールされていること
- 必要なパッケージは `requirements.txt` に記載
- Google Firebase サービスアカウントキー（`config/serviceAccountKey.json`）が配置済み
- WSL/Windows でのポートフォワードが必要な場合は別途設定

## 2. 初回セットアップ
1. 仮想環境の作成（任意）
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. 依存パッケージのインストール
   ```bash
   pip install -r requirements.txt
   ```
3. Firebase サービスアカウントキーの配置
   - `config/serviceAccountKey.json` をGoogle Cloud Consoleから取得し、同名で配置

## 3. データベース初期化（必要に応じて）
- SQLiteの場合：
  ```bash
  sqlite3 fassion.db < scripts/init_db.sql
  ```
- Firestoreの場合：
  - 初期データ投入スクリプト（例：`scripts/seed_wiki_map.py` など）を実行

## 4. サーバーの起動
```bash
python run.py
```
または
```bash
python -m app
```

- デフォルトで `0.0.0.0:5000` で起動
- WSL2環境でWindowsからアクセスする場合はポートフォワード設定が必要

## 5. Webアクセス
- ブラウザで `http://localhost:5000` へアクセス
- ログイン画面が表示される

## 6. 管理者ユーザー作成（初回のみ）
```bash
python scripts/create_admin_user.py
```

## 7. キャッシュ・トレンドデータの更新
- サーバー起動時・定期的に自動でGoogleトレンド・天気・Wikiトレンドのキャッシュが更新されます
- 手動で更新したい場合は `scripts/manual_update.py` などを利用

## 8. その他
- 静的ファイルは `app/static/` 配下、テンプレートは `app/templates/` 配下
- 設定ファイルや環境変数は `.env` または `config/` 配下で管理

---

## トラブルシューティング
- サーバーが起動しない場合：
  - Pythonバージョン、依存パッケージ、サービスアカウントキーの有無を確認
- Googleトレンドが取得できない場合：
  - ネットワーク、API制限、キャッシュファイルの削除・再起動を試す
- ポートフォワードが必要な場合：
  - Windowsの場合はPowerShellで `netsh interface portproxy` を利用

---

## 参考
- 詳細な運用・開発手順は `README.md` も参照
