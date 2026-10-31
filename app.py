"""REVON Hybrid Motorcycle Management System - Flask application.

Routes, generic CRUD for 7 tables, dashboard, tracking, SQL reports, SQL console.
Run locally:  python app.py          (http://127.0.0.1:5000)
"""
import re
import sys
from datetime import date

from flask import (Flask, abort, flash, redirect, render_template, request, url_for)

import config
import db

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

STATUS_COLORS = {
    "Booked": "blue", "In Assembly": "amber", "Delivered": "green", "Cancelled": "red",
    "Available": "green", "On Delivery": "amber", "On Leave": "gray",
    "In Stock": "green", "Reserved": "blue", "Sold": "gray", "In Service": "amber", "Demo": "purple",
}


# ======================================================================== entity definitions
def F(name, label, kind="text", req=False, choices=None, fk=None, default=None, help=None, step=None):
    return dict(name=name, label=label, kind=kind, req=req, choices=choices, fk=fk,
                default=default, help=help, step=step)


ENTITIES = {
    "customers": dict(
        table="customers", pk="customer_id", title="Customers", singular="Customer", icon="👥",
        fields=[F("full_name", "Full Name", req=True), F("company", "Company / Dealership"),
                F("phone", "Phone", req=True), F("email", "Email", "email"),
                F("city", "City", req=True), F("address", "Address")],
        sql="SELECT c.*, (SELECT COUNT(*) FROM orders o WHERE o.customer_id = c.customer_id) AS orders FROM customers c",
        search=["c.full_name", "c.company", "c.phone", "c.email", "c.city"], order="c.customer_id DESC",
        cols=[("customer_id", "#"), ("full_name", "Name"), ("company", "Company"), ("phone", "Phone"),
              ("email", "Email"), ("city", "City"), ("orders", "Orders")]),
    "staff": dict(
        table="staff", pk="staff_id", title="Staff", singular="Staff Member", icon="🧑‍🔧",
        fields=[F("full_name", "Full Name", req=True), F("employee_no", "Employee No", req=True),
                F("phone", "Phone", req=True),
                F("role", "Role", "select", True, ["Sales Advisor", "Technician", "Delivery Rider"], default="Sales Advisor"),
                F("hire_date", "Hire Date", "date", True), F("experience_yrs", "Experience (years)", "int", True, default=0),
                F("status", "Status", "select", True, ["Available", "On Delivery", "On Leave"], default="Available")],
        sql="SELECT s.* FROM staff s", search=["s.full_name", "s.employee_no", "s.phone", "s.role"], order="s.staff_id DESC",
        cols=[("staff_id", "#"), ("full_name", "Name"), ("employee_no", "Emp No"), ("role", "Role"),
              ("phone", "Phone"), ("hire_date", "Hired", "date"), ("experience_yrs", "Exp (yrs)"), ("status", "Status", "badge")]),
    "bikes": dict(
        table="bikes", pk="bike_id", title="Bikes (Inventory)", singular="Bike", icon="🏍️",
        fields=[F("vin", "VIN / Chassis No", req=True),
                F("bike_type", "Bike Type", "select", True, ["City", "Sport", "Eco", "Cargo", "Touring", "Demo"]),
                F("model_name", "Model", req=True), F("color", "Colour", req=True),
                F("make_year", "Make Year", "int", True, default=2026),
                F("battery_kwh", "Battery (kWh)", "number", True, step="0.01"),
                F("status", "Status", "select", True, ["In Stock", "Reserved", "Sold", "In Service", "Demo"], default="In Stock")],
        sql="SELECT b.* FROM bikes b", search=["b.vin", "b.model_name", "b.color", "b.bike_type"], order="b.bike_id DESC",
        cols=[("bike_id", "#"), ("vin", "VIN"), ("bike_type", "Type"), ("model_name", "Model"), ("color", "Colour"),
              ("make_year", "Year"), ("battery_kwh", "Battery kWh"), ("status", "Status", "badge")]),
    "models": dict(
        table="models", pk="model_id", title="Models & Pricing", singular="Model", icon="📋",
        fields=[F("model_name", "Model Name", req=True), F("variant", "Variant", req=True),
                F("engine_cc", "Engine (cc)", "int", True), F("battery_kwh", "Battery (kWh)", "number", True, step="0.01"),
                F("range_km", "Range (km)", "number", True, step="0.01"), F("top_speed_kmh", "Top Speed (km/h)", "int", True),
                F("base_price", "Base Price (PKR)", "number", True, step="0.01")],
        sql="SELECT m.*, (SELECT COUNT(*) FROM orders o WHERE o.model_id = m.model_id) AS orders FROM models m",
        search=["m.model_name", "m.variant"], order="m.model_id DESC",
        cols=[("model_id", "#"), ("model_name", "Model"), ("variant", "Variant"), ("engine_cc", "Engine cc"),
              ("battery_kwh", "kWh"), ("range_km", "Range km"), ("top_speed_kmh", "Top km/h"),
              ("base_price", "Base Price", "money"), ("orders", "Orders")]),
    "orders": dict(
        table="orders", pk="order_id", title="Orders", singular="Order", icon="🧾", detail=True,
        fields=[F("order_no", "Order No", help="Leave blank to auto-generate (RVN-YYYY-####)"),
                F("customer_id", "Customer", "fk", True, fk=("SELECT customer_id AS id, full_name AS a, city AS b FROM customers ORDER BY full_name", "{a} - {b}")),
                F("model_id", "Model", "fk", True, fk=("SELECT model_id AS id, model_name AS a, variant AS b FROM models ORDER BY model_name, variant", "{a} {b}")),
                F("bike_id", "Bike unit (optional)", "fk", fk=("SELECT bike_id AS id, vin AS a, status AS b FROM bikes ORDER BY vin", "{a} [{b}]")),
                F("staff_id", "Assigned staff (optional)", "fk", fk=("SELECT staff_id AS id, full_name AS a, role AS b FROM staff ORDER BY full_name", "{a} ({b})")),
                F("items_desc", "Items / Accessories", req=True),
                F("quantity", "Quantity (bikes)", "int", True, default=1),
                F("order_date", "Order Date", "date", True),
                F("delivery_date", "Delivery Date", "date", help="Auto-filled when status = Delivered"),
                F("status", "Status", "select", True, ["Booked", "In Assembly", "Delivered", "Cancelled"], default="Booked"),
                F("total_price", "Total Price (PKR)", "number", True, default=0, step="0.01",
                  help="Leave 0 to auto-calculate: quantity x model base price")],
        sql="SELECT * FROM v_order_details", search=["order_no", "customer_name", "customer_city", "model_name", "variant", "vin", "staff_name"],
        order="order_id DESC", filter_status=["Booked", "In Assembly", "Delivered", "Cancelled"],
        cols=[("order_no", "Order No", "link"), ("customer_name", "Customer"), ("model_label", "Model"), ("vin", "Bike VIN"),
              ("staff_name", "Staff"), ("quantity", "Qty"), ("order_date", "Ordered", "date"),
              ("total_price", "Total", "money"), ("paid", "Paid", "money"), ("status", "Status", "badge")]),
    "payments": dict(
        table="payments", pk="payment_id", title="Payments", singular="Payment", icon="💳",
        fields=[F("order_id", "Order", "fk", True, fk=("SELECT o.order_id AS id, o.order_no AS a, c.full_name AS b FROM orders o INNER JOIN customers c ON c.customer_id = o.customer_id ORDER BY o.order_id DESC", "{a} - {b}")),
                F("amount", "Amount (PKR)", "number", True, step="0.01"),
                F("method", "Method", "select", True, ["Cash", "Bank Transfer", "Card", "Cheque", "Online", "Installment"]),
                F("payment_date", "Payment Date", "date", True), F("reference_no", "Reference No")],
        sql="SELECT p.*, o.order_no, c.full_name AS customer_name FROM payments p INNER JOIN orders o ON o.order_id = p.order_id INNER JOIN customers c ON c.customer_id = o.customer_id",
        search=["o.order_no", "c.full_name", "p.method", "p.reference_no"], order="p.payment_id DESC",
        cols=[("payment_id", "#"), ("order_no", "Order No"), ("customer_name", "Customer"), ("amount", "Amount", "money"),
              ("method", "Method"), ("payment_date", "Date", "date"), ("reference_no", "Reference")]),
    "service": dict(
        table="service_records", pk="service_id", title="Service Records", singular="Service Record", icon="🔧",
        fields=[F("bike_id", "Bike", "fk", True, fk=("SELECT bike_id AS id, vin AS a, model_name AS b FROM bikes ORDER BY vin", "{a} - {b}")),
                F("service_date", "Service Date", "date", True),
                F("service_type", "Service Type", "select", True, ["Battery Check", "Oil Change", "Tyre", "Engine", "Brakes", "General Service", "Software Update"]),
                F("description", "Description"), F("cost", "Cost (PKR)", "number", True, default=0, step="0.01")],
        sql="SELECT sr.*, b.vin, b.model_name FROM service_records sr INNER JOIN bikes b ON b.bike_id = sr.bike_id",
        search=["b.vin", "b.model_name", "sr.service_type", "sr.description"], order="sr.service_id DESC",
        cols=[("service_id", "#"), ("vin", "Bike VIN"), ("model_name", "Model"), ("service_date", "Date", "date"),
              ("service_type", "Service"), ("description", "Description"), ("cost", "Cost", "money")]),
}
NAV = ["orders", "customers", "bikes", "models", "staff", "payments", "service"]


# ======================================================================== template helpers
@app.template_filter("money")
def money(v):
    try:
        return f"{config.CURRENCY} {float(v):,.0f}"
    except (TypeError, ValueError):
        return "-"


@app.template_filter("num")
def num(v):
    try:
        f = float(v)
        return f"{f:,.0f}" if f.is_integer() else f"{f:,.2f}"
    except (TypeError, ValueError):
        return v if v is not None else "-"


@app.template_filter("badge")
def badge(v):
    return STATUS_COLORS.get(v, "gray")


@app.context_processor
def inject():
    return dict(brand=config.BRAND, company=config.COMPANY, tagline=config.TAGLINE, ENTITIES=ENTITIES, NAV=NAV,
                engine_label=db.engine_label(), engine_note=db.engine_note(), STATUS_COLORS=STATUS_COLORS,
                today=date.today().isoformat(), on_vercel=config.ON_VERCEL)


def post_process(key, rows):
    if key == "orders":
        for r in rows:
            r["model_label"] = f"{r['model_name']} {r['variant']}"
    return rows


def fk_options(field):
    sql, fmt = field["fk"]
    return [(r["id"], fmt.format(**r)) for r in db.query(sql)]


def form_options(ent):
    return {f["name"]: fk_options(f) for f in ent["fields"] if f["kind"] == "fk"}


# ======================================================================== dashboard
@app.route("/")
def dashboard():
    k = db.query("SELECT COUNT(*) AS n, COALESCE(SUM(total_price),0) AS revenue, COALESCE(SUM(quantity),0) AS units FROM orders WHERE status <> 'Cancelled'", one=True)
    paid = db.query("SELECT COALESCE(SUM(p.amount),0) AS paid FROM payments p INNER JOIN orders o ON o.order_id = p.order_id WHERE o.status <> 'Cancelled'", one=True)["paid"]
    stats = dict(orders=k["n"], units=k["units"], revenue=k["revenue"], paid=paid, outstanding=k["revenue"] - paid,
                 customers=db.query("SELECT COUNT(*) AS n FROM customers", one=True)["n"],
                 bikes=db.query("SELECT COUNT(*) AS n FROM bikes", one=True)["n"])
    by_status = db.query("SELECT status, COUNT(*) AS n, COALESCE(SUM(total_price),0) AS value FROM orders GROUP BY status ORDER BY n DESC")
    top_models = db.query("""SELECT m.model_name, m.variant, COALESCE(SUM(o.quantity),0) AS units, COALESCE(SUM(o.total_price),0) AS revenue
                             FROM models m LEFT JOIN orders o ON o.model_id = m.model_id AND o.status <> 'Cancelled'
                             GROUP BY m.model_id, m.model_name, m.variant ORDER BY revenue DESC LIMIT 5""")
    bike_status = db.query("SELECT status, COUNT(*) AS n FROM bikes GROUP BY status ORDER BY n DESC")
    staff_status = db.query("SELECT status, COUNT(*) AS n FROM staff GROUP BY status ORDER BY n DESC")
    recent = db.query("SELECT * FROM v_order_details ORDER BY order_date DESC, order_id DESC LIMIT 6")
    max_rev = max([m["revenue"] for m in top_models] + [1])
    return render_template("dashboard.html", s=stats, by_status=by_status, top_models=top_models, max_rev=max_rev,
                           bike_status=bike_status, staff_status=staff_status, recent=recent)


# ======================================================================== generic CRUD
def get_entity(key):
    ent = ENTITIES.get(key)
    if not ent:
        abort(404)
    return ent


@app.route("/<key>")
def list_page(key):
    ent = get_entity(key)
    q = request.args.get("q", "").strip()
    st = request.args.get("status", "").strip()
    sql, params, where = ent["sql"], [], []
    if q:
        where.append("(" + " OR ".join(f"{c} LIKE %s" for c in ent["search"]) + ")")
        params += [f"%{q}%"] * len(ent["search"])
    if st and ent.get("filter_status"):
        where.append("status = %s")
        params.append(st)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY " + ent["order"]
    rows = post_process(key, db.query(sql, params))
    return render_template("list.html", key=key, ent=ent, rows=rows, q=q, st=st)


def collect(ent):
    values, errors = {}, []
    for f in ent["fields"]:
        raw = (request.form.get(f["name"]) or "").strip()
        if raw == "":
            if f["req"] and f["default"] is None:
                errors.append(f"{f['label']} is required.")
            values[f["name"]] = f["default"] if f["req"] else None
            continue
        try:
            if f["kind"] in ("int", "fk"):
                raw = int(raw)
            elif f["kind"] == "number":
                raw = float(raw)
        except ValueError:
            errors.append(f"{f['label']} must be a number.")
        values[f["name"]] = raw
    return values, errors


def apply_order_rules(v, order_id=None):
    """Business rules for orders (all shown to the user as messages)."""
    notes = []
    if not v.get("order_no"):
        n = db.query("SELECT COUNT(*) AS n FROM orders", one=True)["n"] + 1
        v["order_no"] = f"RVN-{date.today().year}-{n:04d}"
        while db.query("SELECT 1 AS x FROM orders WHERE order_no = %s", (v["order_no"],)):
            n += 1
            v["order_no"] = f"RVN-{date.today().year}-{n:04d}"
        notes.append(f"Order number {v['order_no']} generated automatically.")
    if (not v.get("total_price")) and v.get("model_id") and v.get("quantity"):
        m = db.query("SELECT base_price FROM models WHERE model_id = %s", (v["model_id"],), one=True)
        if m:
            v["total_price"] = float(m["base_price"]) * v["quantity"]
            notes.append(f"Total price auto-calculated: {v['quantity']} x {m['base_price']:,.0f} = {v['total_price']:,.0f}.")
    if v.get("status") == "Delivered" and not v.get("delivery_date"):
        v["delivery_date"] = date.today().isoformat()
        notes.append("Delivery date set to today because status is Delivered.")
    warns = []
    if v.get("bike_id") and v.get("quantity") and v["quantity"] > 1:
        warns.append("A specific bike unit is assigned but the order quantity is more than 1 - assign units individually.")
    if v.get("bike_id"):
        b = db.query("SELECT vin, status FROM bikes WHERE bike_id = %s", (v["bike_id"],), one=True)
        if b and b["status"] in ("Sold", "In Service"):
            warns.append(f"Bike {b['vin']} is currently '{b['status']}', not available stock.")
    if v.get("staff_id"):
        s = db.query("SELECT full_name, status FROM staff WHERE staff_id = %s", (v["staff_id"],), one=True)
        if s and s["status"] == "On Leave":
            warns.append(f"{s['full_name']} is currently on leave.")
    return notes, warns


def save(key, pk=None):
    ent = get_entity(key)
    values, errors = collect(ent)
    notes, warns = [], []
    if not errors and key == "orders":
        notes, warns = apply_order_rules(values, pk)
    if errors:
        for e in errors:
            flash(e, "error")
        return None, values
    cols = [f["name"] for f in ent["fields"]]
    vals = [values[c] for c in cols]
    if pk is None:
        sql = f"INSERT INTO {ent['table']} ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})"
        params = vals
    else:
        sql = f"UPDATE {ent['table']} SET {', '.join(c + ' = %s' for c in cols)} WHERE {ent['pk']} = %s"
        params = vals + [pk]
    try:
        last_id, _ = db.execute(sql, params)
    except db.DBError as exc:
        flash(db.friendly_error(exc), "error")
        return None, values
    for n in notes:
        flash(n, "info")
    for w in warns:
        flash(w, "warn")
    flash(f"{ent['singular']} {'added' if pk is None else 'updated'} successfully.", "success")
    flash(db.render_sql(sql, params), "sql")
    return (pk or last_id), values


@app.route("/<key>/new", methods=["GET", "POST"])
def new_page(key):
    ent = get_entity(key)
    if request.method == "POST":
        new_id, values = save(key)
        if new_id:
            return redirect(url_for("order_detail", order_id=new_id) if key == "orders" else url_for("list_page", key=key))
    else:
        values = {f["name"]: f["default"] for f in ent["fields"]}
        values.update({k: v for k, v in request.args.items()})
        if "order_date" in values and not values["order_date"]:
            values["order_date"] = date.today().isoformat()
        for dn in ("payment_date", "service_date"):
            if dn in values and not values[dn]:
                values[dn] = date.today().isoformat()
    return render_template("form.html", key=key, ent=ent, values=values, options=form_options(ent), editing=False)


@app.route("/<key>/<int:pk>/edit", methods=["GET", "POST"])
def edit_page(key, pk):
    ent = get_entity(key)
    row = db.query(f"SELECT * FROM {ent['table']} WHERE {ent['pk']} = %s", (pk,), one=True)
    if not row:
        abort(404)
    if request.method == "POST":
        done, values = save(key, pk)
        if done:
            return redirect(url_for("order_detail", order_id=pk) if key == "orders" else url_for("list_page", key=key))
    else:
        values = row
    return render_template("form.html", key=key, ent=ent, values=values, options=form_options(ent), editing=True, pk=pk)


@app.route("/<key>/<int:pk>/delete", methods=["POST"])
def delete_page(key, pk):
    ent = get_entity(key)
    sql = f"DELETE FROM {ent['table']} WHERE {ent['pk']} = %s"
    try:
        _, n = db.execute(sql, (pk,))
        flash(f"{ent['singular']} #{pk} deleted." if n else "Nothing was deleted (record not found).", "success" if n else "warn")
        flash(db.render_sql(sql, (pk,)), "sql")
    except db.DBError as exc:
        flash(db.friendly_error(exc), "error")
    return redirect(url_for("list_page", key=key))


# ======================================================================== order detail + tracking
@app.route("/orders/<int:order_id>")
def order_detail(order_id):
    o = db.query("""SELECT o.*, c.full_name AS customer_name, c.phone AS customer_phone, c.email AS customer_email, c.city AS customer_city,
                           m.model_name, m.variant, m.engine_cc, m.battery_kwh AS model_kwh, m.range_km, m.top_speed_kmh, m.base_price,
                           b.vin, b.color, b.status AS bike_status,
                           s.full_name AS staff_name, s.role AS staff_role, s.phone AS staff_phone
                    FROM orders o
                    INNER JOIN customers c ON c.customer_id = o.customer_id
                    INNER JOIN models m    ON m.model_id    = o.model_id
                    LEFT  JOIN bikes b     ON b.bike_id     = o.bike_id
                    LEFT  JOIN staff s     ON s.staff_id    = o.staff_id
                    WHERE o.order_id = %s""", (order_id,), one=True)
    if not o:
        abort(404)
    pays = db.query("SELECT * FROM payments WHERE order_id = %s ORDER BY payment_date", (order_id,))
    paid = sum(p["amount"] for p in pays)
    steps = ["Booked", "In Assembly", "Delivered"]
    idx = steps.index(o["status"]) if o["status"] in steps else -1
    return render_template("order.html", o=o, pays=pays, paid=paid, balance=o["total_price"] - paid, steps=steps, idx=idx)


@app.route("/track")
def track():
    no = request.args.get("no", "").strip().upper()
    if not no:
        return render_template("track.html", no="", found=None)
    row = db.query("SELECT order_id FROM orders WHERE UPPER(order_no) = %s", (no,), one=True)
    if row:
        return redirect(url_for("order_detail", order_id=row["order_id"]))
    flash(f"No order found with number '{no}'. Try RVN-2026-0009.", "error")
    return render_template("track.html", no=no, found=False)


# ======================================================================== SQL reports + console
REPORTS = [
    ("INNER JOIN", "Orders with customer and model (3 tables)",
     """SELECT o.order_no, c.full_name AS customer, m.model_name, m.variant, o.quantity, o.total_price, o.status
FROM orders o
INNER JOIN customers c ON c.customer_id = o.customer_id
INNER JOIN models m ON m.model_id = o.model_id
ORDER BY o.order_id"""),
    ("LEFT JOIN", "All customers, including those with no orders",
     """SELECT c.full_name, c.city, COUNT(o.order_id) AS orders, COALESCE(SUM(o.total_price), 0) AS order_value
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.full_name, c.city
ORDER BY orders DESC, c.full_name"""),
    ("SELF JOIN", "Pairs of customers living in the same city",
     """SELECT a.full_name AS customer_1, b.full_name AS customer_2, a.city
FROM customers a
INNER JOIN customers b ON a.city = b.city AND a.customer_id < b.customer_id
ORDER BY a.city, a.full_name"""),
    ("GROUP BY + HAVING", "Customers who ordered more than PKR 500,000",
     """SELECT c.full_name, COUNT(o.order_id) AS orders, SUM(o.total_price) AS total_value
FROM customers c
INNER JOIN orders o ON o.customer_id = c.customer_id
WHERE o.status <> 'Cancelled'
GROUP BY c.customer_id, c.full_name
HAVING SUM(o.total_price) > 500000
ORDER BY total_value DESC"""),
    ("GROUP BY + aggregates", "Units and revenue by model family",
     """SELECT m.model_name, SUM(o.quantity) AS units, COUNT(o.order_id) AS orders,
       SUM(o.total_price) AS revenue, AVG(o.total_price) AS avg_order
FROM orders o
INNER JOIN models m ON m.model_id = o.model_id
WHERE o.status <> 'Cancelled'
GROUP BY m.model_name
ORDER BY revenue DESC"""),
    ("Correlated sub-query", "Orders that still have a balance due",
     """SELECT o.order_no, o.total_price,
       (SELECT COALESCE(SUM(p.amount), 0) FROM payments p WHERE p.order_id = o.order_id) AS paid
FROM orders o
WHERE o.status <> 'Cancelled'
  AND o.total_price > (SELECT COALESCE(SUM(p.amount), 0) FROM payments p WHERE p.order_id = o.order_id)
ORDER BY o.order_no"""),
    ("NOT IN", "Bikes that have never been serviced",
     """SELECT bike_id, vin, model_name, status
FROM bikes
WHERE bike_id NOT IN (SELECT bike_id FROM service_records)
ORDER BY bike_id"""),
    ("Scalar sub-query", "Models priced above the average base price",
     """SELECT model_name, variant, base_price,
       (SELECT AVG(base_price) FROM models) AS average_price
FROM models
WHERE base_price > (SELECT AVG(base_price) FROM models)
ORDER BY base_price DESC"""),
    ("Aggregates", "Service cost summary: COUNT, SUM, AVG, MAX, MIN",
     """SELECT service_type, COUNT(*) AS jobs, SUM(cost) AS total_cost, AVG(cost) AS avg_cost,
       MAX(cost) AS max_cost, MIN(cost) AS min_cost
FROM service_records
GROUP BY service_type
ORDER BY total_cost DESC"""),
]


@app.route("/reports")
def reports():
    rid = request.args.get("r", 1, type=int)
    if not 1 <= rid <= len(REPORTS):
        abort(404)
    title, desc, sql = REPORTS[rid - 1][0], REPORTS[rid - 1][1], REPORTS[rid - 1][2]
    rows = db.query(sql)
    return render_template("reports.html", reports=REPORTS, rid=rid, title=title, desc=desc, sql=sql, rows=rows)


FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|create|truncate|replace|grant|revoke|attach|detach|pragma|call|load|into|set)\b", re.I)


@app.route("/console", methods=["GET", "POST"])
def console():
    sql = request.form.get("sql", "SELECT * FROM v_order_details LIMIT 10;" if request.method == "GET" else "").strip()
    rows, error = None, None
    if request.method == "POST" and sql:
        stmt = sql.rstrip().rstrip(";").strip()
        first = stmt.split(None, 1)[0].lower() if stmt else ""
        if ";" in stmt:
            error = "Only one statement at a time is allowed."
        elif first not in ("select", "with", "show", "describe", "desc", "explain"):
            error = "Read-only console: only SELECT / SHOW / DESCRIBE statements are allowed."
        elif first in ("select", "with") and FORBIDDEN.search(stmt):
            error = "Write or administrative keywords are blocked in the console."
        else:
            try:
                rows = db.query(stmt)[:500]
            except db.DBError as exc:
                error = f"SQL error: {exc}"
    return render_template("console.html", sql=sql, rows=rows, error=error)


# ======================================================================== about / ERD
@app.route("/about")
def about():
    counts = []
    for key in ["customers", "staff", "bikes", "models", "orders", "payments", "service"]:
        e = ENTITIES[key]
        counts.append((e["table"], db.query(f"SELECT COUNT(*) AS n FROM {e['table']}", one=True)["n"]))
    return render_template("about.html", counts=counts, project=config.PROJECT)


@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404, message="Page or record not found."), 404


@app.errorhandler(Exception)
def server_error(exc):
    if hasattr(exc, "code") and isinstance(exc.code, int) and exc.code < 500:
        return render_template("error.html", code=exc.code, message=str(exc)), exc.code
    return render_template("error.html", code=500, message=f"{type(exc).__name__}: {exc}"), 500


# ======================================================================== CLI
if __name__ == "__main__":
    import os
    if "--reset-sqlite" in sys.argv:
        db.reset_sqlite()
        print("[REVON] SQLite database rebuilt with sample data.")
        sys.exit()
    if "--init-mysql" in sys.argv or "--init-mysql-managed" in sys.argv:
        db.init_mysql(managed="--init-mysql-managed" in sys.argv)
        print(f"[REVON] MySQL database '{config.MYSQL_DATABASE}' created and seeded.")
        sys.exit()
    print(f"[REVON] Connected to {db.engine_label()}  {db.engine_note()}")
    port = int(os.getenv("PORT", "5000"))
    print(f"[REVON] Open  http://127.0.0.1:{port}  in your browser")
    app.run(host="0.0.0.0", port=port, debug=bool(os.getenv("FLASK_DEBUG")))
