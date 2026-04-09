"""
database/db.py
==============
Acceso a datos. SQLite por defecto, PostgreSQL en producción.
Cambia solo get_conn() para migrar entre motores.
"""
import os
import json
import sqlite3
import hashlib
from datetime import datetime
from typing import Optional

DATABASE_URL = os.environ.get("DATABASE_URL", "")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "db.sqlite3")


def get_conn():
    """Retorna (conexión, motor). Motor: 'sqlite' | 'pg'."""
    if DATABASE_URL:
        try:
            import psycopg2
            url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
            conn = psycopg2.connect(url)
            conn.autocommit = True
            return conn, "pg"
        except ImportError:
            raise RuntimeError("Agrega psycopg2-binary a requirements.txt")
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn, "sqlite"


def ph(engine: str) -> str:
    """Placeholder de parámetros según motor."""
    return "%s" if engine == "pg" else "?"


def init_db() -> None:
    """Crea tablas si no existen. Idempotente."""
    conn, engine = get_conn()
    cur = conn.cursor()
    if engine == "sqlite":
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS snapshots (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                clave          TEXT    NOT NULL UNIQUE,
                datos          TEXT    NOT NULL,
                hash_datos     TEXT,
                creado_en      TEXT    DEFAULT (datetime('now')),
                actualizado_en TEXT    DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS sync_log (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario   TEXT,
                accion    TEXT,
                creado_en TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_clave ON snapshots(clave);
        """)
        conn.commit()
    else:
        for sql in [
            """CREATE TABLE IF NOT EXISTS snapshots (
                id SERIAL PRIMARY KEY, clave TEXT NOT NULL UNIQUE,
                datos JSONB NOT NULL, hash_datos TEXT,
                creado_en TIMESTAMPTZ DEFAULT NOW(),
                actualizado_en TIMESTAMPTZ DEFAULT NOW())""",
            """CREATE TABLE IF NOT EXISTS sync_log (
                id SERIAL PRIMARY KEY, usuario TEXT,
                accion TEXT, creado_en TIMESTAMPTZ DEFAULT NOW())""",
            "CREATE INDEX IF NOT EXISTS idx_clave ON snapshots(clave)"
        ]:
            cur.execute(sql)
    conn.close()


def guardar_snapshot(clave: str, datos: dict, usuario: str = "web") -> bool:
    """Inserta o actualiza un snapshot (UPSERT)."""
    try:
        conn, engine = get_conn()
        cur = conn.cursor()
        js  = json.dumps(datos, ensure_ascii=False)
        h   = hashlib.md5(js.encode()).hexdigest()
        ts  = datetime.utcnow().isoformat()
        q   = ph(engine)

        if engine == "sqlite":
            cur.execute("""
                INSERT INTO snapshots (clave, datos, hash_datos, creado_en, actualizado_en)
                VALUES (?,?,?,?,?)
                ON CONFLICT(clave) DO UPDATE SET
                  datos=excluded.datos,
                  hash_datos=excluded.hash_datos,
                  actualizado_en=excluded.actualizado_en
            """, (clave, js, h, ts, ts))
            conn.commit()
        else:
            cur.execute(f"""
                INSERT INTO snapshots (clave, datos, hash_datos, actualizado_en)
                VALUES ({q},{q}::jsonb,{q},NOW())
                ON CONFLICT(clave) DO UPDATE SET
                  datos=EXCLUDED.datos,
                  hash_datos=EXCLUDED.hash_datos,
                  actualizado_en=NOW()
            """, (clave, js, h))

        cur.execute(
            f"INSERT INTO sync_log (usuario, accion) VALUES ({q},{q})",
            (usuario, f"guardar:{clave}")
        )
        if engine == "sqlite":
            conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB] guardar error: {e}")
        return False


def cargar_snapshot(clave: str) -> Optional[dict]:
    """Carga el snapshot más reciente de una clave."""
    try:
        conn, engine = get_conn()
        cur = conn.cursor()
        cur.execute(
            f"SELECT datos, hash_datos, actualizado_en FROM snapshots WHERE clave={ph(engine)}",
            (clave,)
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        raw   = row[0] if engine == "pg" else row["datos"]
        datos = raw if isinstance(raw, dict) else json.loads(raw)
        return {
            "datos":          datos,
            "hash":           row[1] if engine == "pg" else row["hash_datos"],
            "actualizado_en": str(row[2] if engine == "pg" else row["actualizado_en"])
        }
    except Exception as e:
        print(f"[DB] cargar error: {e}")
        return None


def registrar_log(usuario: str, accion: str) -> None:
    """Registra una acción de auditoría."""
    try:
        conn, engine = get_conn()
        cur = conn.cursor()
        q = ph(engine)
        cur.execute(
            f"INSERT INTO sync_log (usuario, accion) VALUES ({q},{q})",
            (usuario, accion)
        )
        if engine == "sqlite":
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB] log error: {e}")
