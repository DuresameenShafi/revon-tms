"""Draws the ERD with Graphviz.  Usage:  python docs/generate_erd.py   (needs `dot` installed)."""
import os
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))

TABLES = {
    "customers": ["customer_id PK", "full_name", "company", "phone UK", "email UK", "city", "address"],
    "models": ["model_id PK", "model_name", "variant", "engine_cc", "battery_kwh", "range_km", "top_speed_kmh", "base_price"],
    "bikes": ["bike_id PK", "vin UK", "bike_type", "model_name", "color", "make_year", "battery_kwh", "status"],
    "staff": ["staff_id PK", "full_name", "employee_no UK", "role", "hire_date", "experience_yrs", "status"],
    "orders": ["order_id PK", "order_no UK", "customer_id FK", "model_id FK", "bike_id FK", "staff_id FK",
               "quantity", "order_date", "delivery_date", "status", "total_price"],
    "payments": ["payment_id PK", "order_id FK", "amount", "method", "payment_date", "reference_no"],
    "service_records": ["service_id PK", "bike_id FK", "service_date", "service_type", "cost"],
}
EDGES = [  # parent, child, label
    ("customers", "orders", "places  1:N"), ("models", "orders", "ordered as  1:N"),
    ("bikes", "orders", "fulfils  1:N (optional)"), ("staff", "orders", "handles  1:N (optional)"),
    ("orders", "payments", "paid by  1:N"), ("bikes", "service_records", "serviced in  1:N"),
]
COLORS = {"orders": "#0e9f6e"}

lines = ['digraph REVON {', ' rankdir=LR; splines=polyline; nodesep=0.5; ranksep=1.1; bgcolor="white";',
         ' node [shape=plain fontname="Helvetica"]; edge [fontname="Helvetica" fontsize=10 color="#475569"];']
for t, cols in TABLES.items():
    head = COLORS.get(t, "#0d1b18")
    rows = "".join(
        f'<TR><TD ALIGN="LEFT" BGCOLOR="{"#fef3c7" if c.endswith("PK") else "#e0f2fe" if c.endswith("FK") else "white"}">{c}</TD></TR>'
        for c in cols)
    lines.append(f' {t} [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="5">'
                 f'<TR><TD BGCOLOR="{head}"><FONT COLOR="white"><B>{t.upper()}</B></FONT></TD></TR>{rows}</TABLE>>];')
for p, c, lab in EDGES:
    lines.append(f' {p} -> {c} [label="{lab}" arrowhead=crowodot arrowtail=tee dir=both];')
lines.append("}")

dot_path = os.path.join(HERE, "erd.dot")
open(dot_path, "w").write("\n".join(lines))
for fmt in ("png", "svg"):
    args = ["dot", f"-T{fmt}"] + (["-Gdpi=150"] if fmt == "png" else []) + [dot_path, "-o", os.path.join(HERE, f"ERD.{fmt}")]
    subprocess.run(args, check=True)
shutil.copy(os.path.join(HERE, "ERD.png"), os.path.join(HERE, "..", "static", "erd.png"))
print("ERD written to docs/ERD.png, docs/ERD.svg and static/erd.png")
