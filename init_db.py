import argparse
import sqlite3
from pathlib import Path

# DB初期化ワンショットスクリプト。
# - schema.sql を丸ごと実行してテーブルをDROP→CREATEし、サンプルデータを投入します。
# - 既存の中身は消えるので、上書きしてよいDBに対してのみ実行してください。
# - 使い方: python init_db.py [--db fassion.db] [--schema schema.sql]


def load_schema(db_path: Path, schema_path: Path) -> None:
    """対象のDBに対してschema.sqlを実行します（テーブルを削除して再作成します）。"""
    sql = schema_path.read_text(encoding="utf-8")
    with sqlite3.connect(db_path) as conn:
        conn.executescript(sql)
        conn.commit()

def main() -> None:
    parser = argparse.ArgumentParser(description="schema.sqlからSQLite DBを初期化します")
    parser.add_argument(
        "--db",
        default="fassion.db",
        help="DBファイルパス（デフォルト: fassion.db）",
    )
    parser.add_argument(
        "--schema",
        default="schema.sql",
        help="スキーマファイルパス（デフォルト: schema.sql）",
    )
    args = parser.parse_args()

    db_path = Path(args.db)
    schema_path = Path(args.schema)

    if not schema_path.exists():
        raise FileNotFoundError(f"スキーマファイルが見つかりません: {schema_path}")

    print(f"DBを初期化しています: {db_path} using {schema_path}")
    load_schema(db_path, schema_path)
    print("完了しました。sqlite3またはアプリケーションでDBを開くことができます。")

if __name__ == "__main__":
    main()
