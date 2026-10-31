"""Database connectivity layer: MySQL (PyMySQL) or SQLite, one tiny API for both.

    query(sql, params)    -> list[dict]
    execute(sql, params)  -> (last_insert_id, rowcount)   (COMMIT / ROLLBACK handled here)

SQL is written once with %s placeholders; they are converted to ? for SQLite.
"""
import os
import re
import sqlite3
from datetime import date, datetime
from decimal import Decimal

import config

try:
    import pymysql
    import pymysql.cursors
except ImportError:  # SQLite-only installs still work
    pymysql = None

DB_DIR = os.path.join(config.BASE_DIR, "database")
_state = {"engine": None, "note": ""}


# ------------------------------------------------------------------ engine choice
def _mysql_connect(with_db=True):
    kw = dict(host=config.MYSQL_HOST, port=config.MYSQL_PORT, user=config.MYSQL_USER,
              password=config.MYSQL_PASSWORD, charset="utf8mb4", connect_timeout=5,
              cursorclass=pymysql.cursors.DictCursor, autocommit=False)
    if with_db:
        kw["database"] = config.MYSQL_DATABASE
    if config.MYSQL_SSL:
        import certifi
        kw["ssl"] = {"ca": certifi.where()}
    return pymysql.connect(**kw)


def engine():
    """Return 'mysql' or 'sqlite' (decided once per process)."""
    if _state["engine"]:
        return _state["engine"]
    want = config.DB_ENGINE
    # On Vercel with no MySQL host configured there is nothing to try
    if want == "auto" and config.ON_VERCEL and not os.getenv("MYSQL_HOST"):
        want = "sqlite"
    if want in ("auto", "mysql") and pymysql is not None:
        try:
            _mysql_connect().close()
            _state.update(engine="mysql", note=f"{config.MYSQL_USER}@{config.MYSQL_HOST}:{config.MYSQL_PORT}/{config.MYSQL_DATABASE}")
            return "mysql"
        except Exception as exc:  # noqa: BLE001
            if want == "mysql":
                raise
            print(f"[REVON] MySQL not available ({exc}); using SQLite instead.")
    _state.update(engine="sqlite", note=config.SQLITE_PATH)
    _ensure_sqlite()
    return "sqlite"


def engine_label():
    e = engine()
    return "MySQL" if e == "mysql" else "SQLite"


def engine_note():
    engine()
    return _state["note"]


def placeholder(sql):
    return sql.replace("%s", "?") if engine() == "sqlite" else sql


# ------------------------------------------------------------------ SQLite bootstrap
def _read(name):
    with open(os.path.join(DB_DIR, name), encoding="utf-8") as fh:
        return fh.read()


def _ensure_sqlite(force=False):
    path = config.SQLITE_PATH
    if force and os.path.exists(path):
        os.remove(path)
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    con = sqlite3.connect(path)
    con.executescript(_read("schema_sqlite.sql"))
    seed = "\n".join(l for l in _read("02_seed_data.sql").splitlines() if not l.strip().upper().startswith("USE "))
    con.executescript(seed)
    con.commit()
    con.close()


def reset_sqlite():
    _ensure_sqlite(force=True)


# ------------------------------------------------------------------ MySQL bootstrap
def _split_sql(text):
    out = []
    for stmt in re.sub(r"--[^\n]*", "", text).split(";"):
        if stmt.strip():
            out.append(stmt.strip())
    return out


def init_mysql(managed=False):
    """Create schema + seed data in MySQL. managed=True skips CREATE DATABASE/USE (hosted DBs)."""
    schema = _read("01_schema_mysql.sql")
    seed = _read("02_seed_data.sql")
    if managed:
        schema = re.sub(r"-- BEGIN-DB-SETUP.*?-- END-DB-SETUP", "", schema, flags=re.S)
        seed = "\n".join(l for l in seed.splitlines() if not l.strip().upper().startswith("USE "))
        con = _mysql_connect(with_db=True)
        # hosted databases: start clean so re-running is safe
        with con.cursor() as cur:
            cur.execute("SET FOREIGN_KEY_CHECKS=0")
            cur.execute("SHOW FULL TABLES")
            for row in cur.fetchall():
                name, kind = list(row.values())[0], list(row.values())[1]
                cur.execute(f"DROP {'VIEW' if 'VIEW' in kind else 'TABLE'} IF EXISTS `{name}`")
            cur.execute("SET FOREIGN_KEY_CHECKS=1")
        con.commit()
    else:
        con = _mysql_connect(with_db=False)
        schema = schema.replace("revon_db", config.MYSQL_DATABASE)
        seed = seed.replace("revon_db", config.MYSQL_DATABASE)
    with con.cursor() as cur:
        for stmt in _split_sql(schema) + _split_sql(seed):
            cur.execute(stmt)
    con.commit()
    con.close()
    _state["engine"] = None


# ------------------------------------------------------------------ query helpers
def _connect():
    if engine() == "mysql":
        return _mysql_connect()
    con = sqlite3.connect(config.SQLITE_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def _clean(v):
    """Make values template/JSON friendly (Decimal -> float, date -> ISO string)."""
    if isinstance(v, Decimal):
        f = float(v)
        return int(f) if f.is_integer() else f
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, date):
        return v.isoformat()
    return v


def _rows(cur):
    return [{k: _clean(v) for k, v in dict(r).items()} for r in cur.fetchall()]


def query(sql, params=(), one=False):
    con = _connect()
    try:
        cur = con.cursor()
        cur.execute(placeholder(sql), tuple(params))
        rows = _rows(cur)
    finally:
        con.close()
    return (rows[0] if rows else None) if one else rows


def execute(sql, params=()):
    """Run one write statement as a transaction: COMMIT on success, ROLLBACK on error."""
    con = _connect()
    try:
        cur = con.cursor()
        cur.execute(placeholder(sql), tuple(params))
        con.commit()
        return cur.lastrowid, cur.rowcount
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def render_sql(sql, params=()):
    """Human-readable SQL (values inlined) shown in the UI after every write."""
    params = list(params)

    def lit(v):
        if v is None:
            return "NULL"
        if isinstance(v, (int, float)):
            return str(v)
        return "'" + str(v).replace("'", "''") + "'"

    out = []
    for part in re.split(r"(%s)", sql):
        out.append(lit(params.pop(0)) if part == "%s" and params else part)
    return re.sub(r"\s+", " ", "".join(out)).strip() + ";"


# ------------------------------------------------------------------ friendly errors
def friendly_error(exc):
    msg = str(exc)
    code = exc.args[0] if exc.args and isinstance(exc.args[0], int) else None
    low = msg.lower()
    if code == 1062 or "unique constraint" in low:
        return "Duplicate value: a record with the same unique field (phone, email, order no, VIN, ...) already exists. [UNIQUE constraint]"
    if code == 1451 or ("foreign key" in low and "delete" in low):
        return "Cannot delete: other records still reference this one. [FOREIGN KEY - ON DELETE RESTRICT]"
    if code == 1452 or "foreign key constraint failed" in low:
        return "Invalid reference: the selected customer / model / bike / staff does not exist (or is still referenced by other rows). [FOREIGN KEY]"
    if code in (3819, 4025) or "check constraint" in low:
        return "A value breaks a CHECK rule (e.g. quantity must be > 0, delivery date cannot be before order date, status must be a valid option). [CHECK constraint]"
    if code in (1048, 1364) or "not null" in low:
        return "A required field is empty. [NOT NULL constraint]"
    if code == 1406 or "too long" in low:
        return "A value is too long for its column."
    return f"Database error: {msg}"


IntegrityErrors = (sqlite3.IntegrityError,) + ((pymysql.err.IntegrityError, pymysql.err.OperationalError, pymysql.err.DataError) if pymysql else ())
DBError = (sqlite3.Error,) + ((pymysql.err.MySQLError,) if pymysql else ())
