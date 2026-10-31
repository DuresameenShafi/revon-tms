"""REVON Hybrid Motorcycle Management System - configuration.

Everything can be overridden with environment variables, so the same code runs
on a laptop (MySQL / SQLite) and on Vercel (SQLite in /tmp or a hosted MySQL).
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ON_VERCEL = bool(os.getenv("VERCEL"))

# "auto"  -> try MySQL first, fall back to SQLite
# "mysql" -> MySQL only      "sqlite" -> SQLite only
DB_ENGINE = os.getenv("DB_ENGINE", "auto").lower()

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")  # <-- put YOUR MySQL password here
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "revon_db")
MYSQL_SSL = os.getenv("MYSQL_SSL", "").lower() in ("1", "true", "yes")  # needed by most hosted MySQL

# SQLite file: Vercel's filesystem is read-only except /tmp (data there is temporary)
SQLITE_PATH = os.getenv(
    "SQLITE_PATH",
    "/tmp/revon.db" if ON_VERCEL else os.path.join(BASE_DIR, "database", "revon.db"),
)

SECRET_KEY = os.getenv("SECRET_KEY", "revon-dev-secret-change-me")

# Branding / project profile (edit freely)
BRAND = "REVON"
COMPANY = "NEXGEN"
TAGLINE = "Hybrid Motorcycle Management System"
PROJECT = {
    "Company": "NEXGEN - Karachi, Pakistan",
    "Product": "REVON hybrid (EV + ICE) motorcycle",
    "Project": "Web database application: ERD -> MySQL -> Flask",
    "Currency": "PKR",
}
CURRENCY = "PKR"
