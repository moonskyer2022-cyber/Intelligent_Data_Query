"""Check and apply only non-destructive schema compatibility changes."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pymysql

from settings import DB_CONNECT_TIMEOUT, DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_READ_TIMEOUT, DB_USER, DB_WRITE_TIMEOUT


REQUIRED_COLUMNS = {
    "product": {"product_name": "VARCHAR(200) NULL", "price": "DECIMAL(14,2) NOT NULL DEFAULT 0", "stock": "INT NOT NULL DEFAULT 0"},
    "category": {"category_name": "VARCHAR(100) NULL"},
    "user": {"user_name": "VARCHAR(100) NULL"},
    "orders": {"order_status": "VARCHAR(40) NULL", "total_amount": "DECIMAL(14,2) NOT NULL DEFAULT 0"},
    "order_item": {"quantity": "INT NOT NULL DEFAULT 1", "line_amount": "DECIMAL(14,2) NOT NULL DEFAULT 0"},
    "query_example": {"question": "VARCHAR(500) NULL", "is_active": "TINYINT NOT NULL DEFAULT 1"},
    "schema_metadata": {"table_name": "VARCHAR(80) NULL", "column_name": "VARCHAR(80) NULL", "is_metric": "TINYINT NOT NULL DEFAULT 0", "sort_order": "INT NOT NULL DEFAULT 0"},
}


def connect():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        connect_timeout=DB_CONNECT_TIMEOUT,
        read_timeout=DB_READ_TIMEOUT,
        write_timeout=DB_WRITE_TIMEOUT,
        autocommit=True,
    )


def inspect_schema(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT TABLE_NAME, COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s", (DB_NAME,))
        tables = {}
        for table, column in cur.fetchall():
            tables.setdefault(table, set()).add(column)
    return tables


def main() -> int:
    parser = argparse.ArgumentParser(description="检查并兼容智能问数 Demo 数据库结构")
    parser.add_argument("--apply", action="store_true", help="仅添加缺失字段，不删除或覆盖已有数据")
    args = parser.parse_args()

    try:
        conn = connect()
    except Exception as exc:
        print(f"数据库连接失败: {exc}", file=sys.stderr)
        return 2

    try:
        if args.apply:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS aiquery_schema_version (
                        component VARCHAR(80) PRIMARY KEY,
                        version INT NOT NULL,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )

        tables = inspect_schema(conn)
        missing_tables = sorted(set(REQUIRED_COLUMNS) - set(tables))
        if missing_tables:
            print(f"缺少必要数据表: {', '.join(missing_tables)}", file=sys.stderr)
            print("请先执行 scripts/init_mysql.sql 或提供正式迁移脚本。", file=sys.stderr)
            return 3

        missing = []
        for table, columns in REQUIRED_COLUMNS.items():
            for column, definition in columns.items():
                if column not in tables[table]:
                    missing.append((table, column, definition))

        if missing and args.apply:
            with conn.cursor() as cur:
                for table, column, definition in missing:
                    cur.execute(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {definition}")
            tables = inspect_schema(conn)

        if missing:
            print("缺少字段:")
            for table, column, _ in missing:
                print(f"- {table}.{column}")
            return 4

        if args.apply:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO aiquery_schema_version (component, version) VALUES ('demo-contract', 1) "
                    "ON DUPLICATE KEY UPDATE version = VALUES(version)"
                )
        print(f"Demo schema contract v1 OK: {len(tables)} tables checked ({'applied' if args.apply else 'read-only check'})")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
