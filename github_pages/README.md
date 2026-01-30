# MyStyle Lite (GitHub Pages Edition)

Flask 版 MyStyle Home/Trends/Weather の UI をほぼそのまま静的化したビルドです。アプリ側で生成しているキャッシュやアイテムデータを JSON に書き出し、この `github_pages/` 配下に配置することで GitHub Pages だけでプレビューできます。

## データの流れ

| 参照元 | エクスポート手段 | Pages 側ファイル |
| --- | --- | --- |
| `Firestore items` | 既存スクリプト or 手動で CSV → JSON | `data/items.json` |
| `user style master` | `style_wiki_map` などから抽出 | `data/styles.json` |
| `instance/weather_cache.json` | そのままコピー | `data/weather.json` |
| `instance/wiki_trend_cache.json` | そのままコピー | `data/wiki_trends.json` |
| 最近見た / お気に入り | 任意でダミー or エクスポート | `data/history.json`, `data/saved_items.json` |

※ Pages 公開時にはリポジトリに含まれる JSON がそのまま表示されるため、公開して問題のないデータのみを配置してください。

## デプロイ手順

1. `github_pages/data/` 以下に最新の JSON を配置します（必要に応じて `scripts/` でエクスポートスクリプトを実行）。
2. `github_pages/` ディレクトリの内容を GitHub にコミットします。
3. GitHub Pages の設定で
	 - **Source:** Deploy from a branch
	 - **Branch:** `main` (例) / folder: `/github_pages`
	 を指定すると、そのまま公開されます。

ローカル確認は VS Code の Live Server もしくは `python -m http.server` で OK です。

### Firestore から静的データを吐き出す

新しく追加した `scripts/export_static_payload.py` を使うと、Firestore の `items` コレクションと `instance/` のキャッシュをまとめて `github_pages/data/` に出力できます。

```bash
python scripts/export_static_payload.py --limit 80 --history 6 --saved 6
```

- `config/serviceAccountKey.json` を参照して Firestore に接続します。
- `items.json` / `styles.json` / `history.json` / `saved_items.json` を自動生成します。
- `instance/weather_cache.json` と `instance/wiki_trend_cache.json` が存在すれば、それぞれ `weather.json` / `wiki_trends.json` にコピーします。
- `--limit`・`--history`・`--saved` で出力件数を調整できます。

## 実装メモ

- `style.css` は Flask 本体と同じ定義をコピーしているため、見た目・間隔は本番画面と一致します。
- `app.js` は下記の振る舞いを持ちます。
	- `localStorage` を使って選択中の系統を保存（Cookie なしでも動作）。
	- `data/*.json` を fetch し、ホーム画面に描画。ファイルが欠けている場合は警告テキストを表示。
	- 天気ロジックは Flask の `build_weather_rules` を縮約し、`weather_tags` と突き合わせて推薦を作ります。
	- Wikipedia トレンドは `wiki_trend_cache.json` の内容をそのままカード化。

## 追加でやりたいこと

- Firestore から `items.json` を吐き出す CLI を `scripts/` に追加すれば、静的ビルドの更新がワンコマンドになります。
- GitHub Actions で「main ブランチへ push → `github_pages/data/` を最新キャッシュで上書き → `gh-pages` ブランチへ配備」という自動化も可能です。
- 認証やユーザー履歴を簡易的に再現したい場合は `localStorage` を更に活用して、「最近見た」「お気に入り」をブラウザ内で完結させる実装を追加できます。
