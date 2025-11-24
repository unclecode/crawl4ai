import sqlite3
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any

class DatabaseManager:
    def __init__(self, db_path=None, schema_path='schema.yaml'):
        self.schema = self._load_schema(schema_path)
        # Use provided path or fallback to schema default
        self.db_path = db_path or self.schema['database']['name']
        self.conn = None
        self._init_database()

    def _load_schema(self, path: str) -> Dict:
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def _init_database(self):
        """Auto-create/migrate database from schema"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        for table_name, table_def in self.schema['tables'].items():
            self._create_or_update_table(table_name, table_def['columns'])

    def _create_or_update_table(self, table_name: str, columns: Dict):
        cursor = self.conn.cursor()

        # Check if table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        table_exists = cursor.fetchone() is not None

        if not table_exists:
            # Create table
            col_defs = []
            for col_name, col_spec in columns.items():
                col_def = f"{col_name} {col_spec['type']}"
                if col_spec.get('primary'):
                    col_def += " PRIMARY KEY"
                if col_spec.get('autoincrement'):
                    col_def += " AUTOINCREMENT"
                if col_spec.get('unique'):
                    col_def += " UNIQUE"
                if col_spec.get('required'):
                    col_def += " NOT NULL"
                if 'default' in col_spec:
                    default = col_spec['default']
                    if default == 'CURRENT_TIMESTAMP':
                        col_def += f" DEFAULT {default}"
                    elif isinstance(default, str):
                        col_def += f" DEFAULT '{default}'"
                    else:
                        col_def += f" DEFAULT {default}"
                col_defs.append(col_def)

            create_sql = f"CREATE TABLE {table_name} ({', '.join(col_defs)})"
            cursor.execute(create_sql)
        else:
            # Check for new columns and add them
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_columns = {row[1] for row in cursor.fetchall()}

            for col_name, col_spec in columns.items():
                if col_name not in existing_columns:
                    col_def = f"{col_spec['type']}"
                    if 'default' in col_spec:
                        default = col_spec['default']
                        if default == 'CURRENT_TIMESTAMP':
                            col_def += f" DEFAULT {default}"
                        elif isinstance(default, str):
                            col_def += f" DEFAULT '{default}'"
                        else:
                            col_def += f" DEFAULT {default}"

                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}")

        self.conn.commit()

    def get_all(self, table: str, limit: int = 100, offset: int = 0, where: str = None) -> List[Dict]:
        cursor = self.conn.cursor()
        query = f"SELECT * FROM {table}"
        if where:
            query += f" WHERE {where}"
        query += f" LIMIT {limit} OFFSET {offset}"

        cursor.execute(query)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def search(self, query: str, tables: List[str] = None) -> Dict[str, List[Dict]]:
        if not tables:
            tables = list(self.schema['tables'].keys())

        results = {}
        cursor = self.conn.cursor()

        for table in tables:
            # Search in text columns
            columns = self.schema['tables'][table]['columns']
            text_cols = [col for col, spec in columns.items()
                        if spec['type'] == 'TEXT' and col != 'id']

            if text_cols:
                where_clause = ' OR '.join([f"{col} LIKE ?" for col in text_cols])
                params = [f'%{query}%'] * len(text_cols)

                cursor.execute(f"SELECT * FROM {table} WHERE {where_clause} LIMIT 10", params)
                rows = cursor.fetchall()
                if rows:
                    results[table] = [dict(row) for row in rows]

        return results

    def close(self):
        if self.conn:
            self.conn.close()