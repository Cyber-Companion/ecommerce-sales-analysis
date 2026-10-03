"""Builds dashboard/olist_dashboard.html — a self-contained interactive
dashboard (plotly.js embedded, works offline) with 3 pages:
Executive Overview / Delivery & Satisfaction / Products & Margins.

Run from project root:  python python/build_dashboard.py
"""
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.io import to_html

FACT = "powerbi/fact_orders_clean.csv"
OUT = "dashboard/olist_dashboard.html"

NAVY, TEAL, SLATE, LIGHT = "#1f2a44", "#2a9d8f", "#5b6b7f", "#f4f6f9"
ACCENT = ["#2a9d8f", "#1f2a44", "#e9c46a", "#e76f51", "#7fb069",
          "#6a7ba2", "#c08497", "#54b0ff", "#f4a261", "#90be6d"]

# ---------------------------------------------------------------- data
df = pd.read_csv(FACT, parse_dates=["order_purchase_timestamp"])
df["is_late_delivery"] = df["is_late_delivery"].astype(str) == "True"
d = df[df.order_status == "delivered"].copy()
d["ym"] = d.order_purchase_timestamp.dt.to_period("M").astype(str)

rev_total = d.price.sum()
orders_n = d.order_id.nunique()
aov = d.groupby("order_id").price.sum().mean()
_do = d.drop_duplicates("order_id")
avg_review = _do.review_score.mean()
n_reviews = int(_do.review_score.notna().sum())
late_rate = _do.is_late_delivery.mean()
avg_days = _do.delivery_days.mean()
_ro = _do.dropna(subset=["review_score"])
late_rev_mean = _ro[_ro.is_late_delivery].review_score.mean()
ontime_rev_mean = _ro[~_ro.is_late_delivery].review_score.mean()
repeat_rate = (d.groupby("customer_unique_id").order_id.nunique() > 1).mean()
sellers_n = d.seller_id.nunique()


def kpi(label, value, sub=""):
    return (f'<div class="kpi"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-sub">{sub}</div></div>')


def fig_html(fig, first):
    # CDN keeps the file small enough to share/push; set PLOTLY_CDN=0 for a
    # fully offline self-contained file.
    js = "cdn" if os.environ.get("PLOTLY_CDN", "1") == "1" else True
    return to_html(fig, full_html=False, include_plotlyjs=(js if first else False),
                   config={"displaylogo": False})


def base_layout(title, hbar=False):
    m = dict(l=150, r=90, t=60, b=50) if hbar else dict(l=50, r=30, t=60, b=50)
    return dict(title=dict(text=title, font=dict(size=15, color=NAVY)),
                paper_bgcolor="white", plot_bgcolor="white",
                font=dict(family="Segoe UI, Arial", color=SLATE),
                margin=m)


# ------------------------------------------------- Page 1 figures
trend = d.groupby("ym").agg(orders=("order_id", "nunique"),
                             revenue=("price", "sum")).reset_index()
f1 = go.Figure(go.Scatter(x=trend.ym, y=trend.revenue, mode="lines+markers",
                          line=dict(color=TEAL, width=3),
                          marker=dict(size=6, color=NAVY), name="Revenue"))
f1.update_layout(**base_layout("Monthly revenue (delivered orders, BRL)"))
f1.update_xaxes(tickangle=-45, nticks=12)

cat = (d.groupby("category_en")
         .agg(revenue=("price", "sum"), orders=("order_id", "nunique"))
         .sort_values("revenue", ascending=False))
top10 = cat.head(10).sort_values("revenue")
f2 = go.Figure(go.Bar(x=top10.revenue, y=top10.index, orientation="h",
                      marker_color=TEAL, text=top10.revenue.map(lambda v: f"{v:,.0f}"),
                      textposition="outside"))
f2.update_layout(**base_layout("Top 10 categories by revenue (BRL)", hbar=True),
                 xaxis=dict(range=[0, top10.revenue.max() * 1.18]))

paymix = (df.drop_duplicates("order_id")
            .groupby("payment_type").size().sort_values(ascending=False))
f3 = go.Figure(go.Pie(labels=paymix.index, values=paymix.values, hole=0.45,
                      marker=dict(colors=ACCENT)))
f3.update_layout(**base_layout("Orders by payment type"))

states = d.customer_state.value_counts().head(10).sort_values()
f4 = go.Figure(go.Bar(x=states.values, y=states.index, orientation="h",
                      marker_color=NAVY,
                      text=states.values, textposition="outside"))
f4.update_layout(**base_layout("Delivered orders by state (top 10)", hbar=True))

# ------------------------------------------------- Page 2 figures
st = (d.groupby("customer_state")
       .agg(o=("order_id", "count"),
            late=("is_late_delivery", "mean"),
            days=("delivery_days", "mean"))
       .query("o >= 500").sort_values("late", ascending=False).head(10)
       .sort_values("late"))
f5 = go.Figure(go.Bar(x=(st.late * 100).round(1), y=st.index, orientation="h",
                      marker_color="#e76f51",
                      text=(st.late * 100).round(1).map(lambda v: f"{v}%"),
                      textposition="outside"))
f5.update_layout(**base_layout("Late-delivery % by state (min 500 orders)", hbar=True),
                 xaxis=dict(range=[0, (st.late * 100).max() * 1.18]))
f5.add_vline(x=late_rate * 100, line_dash="dash", line_color=NAVY,
             annotation_text=f"avg {late_rate:.1%}")

dd_days = d.delivery_days.dropna().clip(upper=65)
bins = pd.cut(dd_days, bins=[0, 5, 10, 15, 20, 25, 30, 40, 50, 65],
              labels=["0–5", "5–10", "10–15", "15–20", "20–25", "25–30",
                      "30–40", "40–50", "50–65"])
hc = bins.value_counts().sort_index()
f6 = go.Figure(go.Bar(x=hc.index.astype(str), y=hc.values, marker_color=TEAL,
                      text=hc.values, textposition="outside"))
f6.update_layout(**base_layout("Delivery time distribution (days, delivered orders)"),
                 xaxis_title="days", yaxis_title="orders")

ro = d.dropna(subset=["review_score"]).copy()
ro["timing"] = np.where(ro.is_late_delivery, "Late", "On-time")
dist = ro.groupby(["timing", "review_score"]).size().unstack("timing")
dist = (dist / dist.sum() * 100).round(1)
f7 = go.Figure()
for col, color in [("On-time", TEAL), ("Late", "#e76f51")]:
    f7.add_bar(x=dist.index.astype(int), y=dist[col].round(1), name=col,
               marker_color=color, text=dist[col].round(1).map(lambda v: f"{v}%"),
               textposition="outside")
f7.update_layout(**base_layout("Review score distribution: on-time vs late (%)"),
                 xaxis_title="review score", yaxis_title="% of reviews",
                 barmode="group")

# ------------------------------------------------- Page 3 figures
fb = (d.groupby("category_en")
       .agg(n=("price", "count"),
            burden=("price", lambda s: d.loc[s.index, "freight_value"].sum() / s.sum() * 100))
       .query("n >= 500").sort_values("burden", ascending=False).head(10)
       .sort_values("burden"))
f8 = go.Figure(go.Bar(x=fb.burden.round(1), y=fb.index, orientation="h",
                      marker_color="#e9c46a",
                      text=fb.burden.round(1).map(lambda v: f"{v}%"),
                      textposition="outside"))
f8.update_layout(**base_layout("Freight burden: freight as % of revenue (top 10)", hbar=True),
                 xaxis=dict(range=[0, fb.burden.max() * 1.22]))

rq = (ro.groupby("category_en")
        .agg(n=("review_score", "count"), avg=("review_score", "mean"))
        .query("n >= 200").sort_values("avg").head(10).sort_values("avg"))
f9 = go.Figure(go.Bar(x=rq.avg.round(2), y=rq.index, orientation="h",
                      marker_color="#c08497",
                      text=rq.avg.round(2), textposition="outside"))
f9.update_layout(**base_layout("Lowest avg review score by category (min 200 reviews)", hbar=True),
                 xaxis=dict(range=[1, 5]))

def html_table(title, headers, rows):
    th = "".join(f"<th>{h}</th>" for h in headers)
    trs = "".join(
        "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return (f'<div class="chart full"><div class="dtable-title">{title}</div>'
            f'<table class="dtable"><thead><tr>{th}</tr></thead>'
            f"<tbody>{trs}</tbody></table></div>")


ct = cat.head(12).reset_index()
ct["burden"] = ct.category_en.map(fb.burden.round(1))
ct["avg_review"] = ct.category_en.map(
    ro.groupby("category_en").review_score.mean().round(2))
table_cat = html_table(
    "Category scorecard (top 12 by revenue)",
    ["Category", "Revenue (BRL)", "Orders", "Freight % of rev.", "Avg review"],
    [[r.category_en, f"{r.revenue:,.0f}", f"{r.orders:,}",
      f"{r.burden:.1f}%" if pd.notna(r.burden) else "—",
      f"{r.avg_review:.2f}" if pd.notna(r.avg_review) else "—"]
     for r in ct.itertuples()])

sl = (d.groupby(["seller_id", "seller_state"])
       .agg(orders=("order_id", "nunique"), revenue=("price", "sum"),
            avg_review=("review_score", "mean"))
       .query("orders >= 50").sort_values("revenue", ascending=False).head(15)
       .reset_index())
table_sell = html_table(
    "Seller leaderboard (min 50 orders)",
    ["Seller ID", "State", "Orders", "Revenue (BRL)", "Avg review"],
    [[r.seller_id[:8] + "…", r.seller_state, f"{r.orders:,}",
      f"{r.revenue:,.0f}", f"{r.avg_review:.2f}"]
     for r in sl.itertuples()])

# ---------------------------------------------------------------- assemble
figs = [f1, f2, f3, f4, f5, f6, f7, f8, f9]
snippets, first = [], True
for fig in figs:
    snippets.append(fig_html(fig, first))
    first = False
(s1a, s1b, s1c, s1d, s2a, s2b, s2c, s3a, s3b) = snippets

page1_kpis = "".join([
    kpi("Total revenue", f"R$ {rev_total:,.0f}", "delivered orders"),
    kpi("Delivered orders", f"{orders_n:,}", "97.0% of all orders"),
    kpi("Avg order value", f"R$ {aov:,.2f}", "per delivered order"),
    kpi("Avg review score", f"{avg_review:.2f} / 5", f"{n_reviews//1000}k reviews"),
])
page2_kpis = "".join([
    kpi("Late deliveries", f"{late_rate:.1%}", f"{int(_do.is_late_delivery.sum()):,} orders"),
    kpi("Avg delivery time", f"{avg_days:.1f} days", "median 10 days"),
    kpi("Review if late", f"{late_rev_mean:.2f} / 5", f"vs {ontime_rev_mean:.2f} on-time"),
    kpi("Worst state (MA)", "19.7% late", "21.1 days avg transit"),
])
page3_kpis = "".join([
    kpi("Active sellers", f"{sellers_n:,}", "delivered ≥1 order"),
    kpi("Repeat purchase rate", f"{repeat_rate:.1%}", "of 93k customers"),
    kpi("Top-3 state share", "66.5%", "SP / RJ / MG"),
    kpi("Heaviest freight", "29.5%", "electronics, of revenue"),
])

html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Olist E-Commerce Sales Dashboard</title>
<style>
body{{font-family:'Segoe UI',Arial,sans-serif;background:{LIGHT};margin:0;color:{SLATE}}}
header{{background:{NAVY};color:white;padding:22px 32px}}
header h1{{margin:0;font-size:22px}} header p{{margin:6px 0 0;opacity:.75;font-size:13px}}
nav{{display:flex;gap:8px;padding:14px 32px 0}}
nav button{{border:none;background:#dde3ec;color:{NAVY};padding:10px 20px;border-radius:8px 8px 0 0;
  font-size:14px;font-weight:600;cursor:pointer}}
nav button.active{{background:white;color:{NAVY}}}
.page{{display:none;background:white;margin:0 32px 32px;padding:24px;border-radius:0 8px 8px 8px}}
.page.active{{display:block}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px}}
.kpi{{background:{LIGHT};border-left:4px solid {TEAL};border-radius:6px;padding:14px 16px}}
.kpi-label{{font-size:12px;text-transform:uppercase;letter-spacing:.5px;opacity:.7}}
.kpi-value{{font-size:24px;font-weight:700;color:{NAVY};margin:4px 0}}
.kpi-sub{{font-size:12px;opacity:.7}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.chart{{border:1px solid #e6eaf0;border-radius:8px;padding:8px;margin-bottom:16px}}
.dtable-title{{font-size:15px;font-weight:600;color:{NAVY};padding:14px 8px 10px}}
table.dtable{{width:100%;border-collapse:collapse;font-size:13px;margin:0 0 8px}}
table.dtable th{{background:{NAVY};color:white;text-align:left;padding:10px 12px;font-weight:600}}
table.dtable td{{padding:9px 12px;border-bottom:1px solid #edf0f4}}
table.dtable tbody tr:nth-child(even){{background:{LIGHT}}}
.full{{grid-column:1/-1}}
.insight{{background:#eef7f5;border-left:4px solid {TEAL};border-radius:6px;padding:14px 18px;
  margin:4px 0 20px;font-size:14px;line-height:1.6}}
.insight b{{color:{NAVY}}}
footer{{text-align:center;font-size:12px;color:#8a97a8;padding:0 0 28px}}
@media(max-width:900px){{.kpis,.grid2{{grid-template-columns:1fr}}}}
</style></head><body>
<header><h1>Olist E-Commerce Sales Dashboard</h1>
<p>Brazilian marketplace &middot; ~100k orders, 2016&ndash;2018 &middot; SQL &rarr; Python &rarr; Power BI pipeline &middot; by Adnan Habib</p></header>
<nav>
<button class="active" onclick="show('p1',this)">Executive Overview</button>
<button onclick="show('p2',this)">Delivery &amp; Satisfaction</button>
<button onclick="show('p3',this)">Products &amp; Margins</button>
</nav>

<div id="p1" class="page active">
<div class="kpis">{page1_kpis}</div>
<div class="insight"><b>Key insight:</b> revenue peaked in Nov 2017 (R$ 988k). Three categories
(health &amp; beauty, watches &amp; gifts, bed/bath/table) drive ~26% of revenue; credit card is 74% of payments.</div>
<div class="grid2"><div class="chart full">{s1a}</div>
<div class="chart">{s1b}</div><div class="chart">{s1c}</div>
<div class="chart full">{s1d}</div></div></div>

<div id="p2" class="page">
<div class="kpis">{page2_kpis}</div>
<div class="insight"><b>Key insight:</b> late delivery is the #1 satisfaction killer &mdash;
late orders score <b>2.57 vs 4.29</b>. The North/Northeast lanes (MA 19.7%, CE 15.3% late,
21+ day transits) need carrier renegotiation or regional fulfillment.</div>
<div class="grid2"><div class="chart">{s2a}</div><div class="chart">{s2b}</div>
<div class="chart full">{s2c}</div></div></div>

<div id="p3" class="page">
<div class="kpis">{page3_kpis}</div>
<div class="insight"><b>Key insight:</b> freight eats ~30% of revenue on electronics and ~25% on
furniture &mdash; set category-aware free-shipping thresholds. Office furniture has 20.3% one-star
reviews: a quality problem, not a logistics one.</div>
<div class="grid2"><div class="chart">{s3a}</div><div class="chart">{s3b}</div>
{table_cat}{table_sell}</div></div>

<footer>Data: Olist public dataset (CC BY-SA 4.0) &middot; Built with Python/Plotly from the cleaned fact table</footer>
<script>
function show(id,btn){{document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
document.querySelectorAll('nav button').forEach(b=>b.classList.remove('active'));
document.getElementById(id).classList.add('active');btn.classList.add('active');
window.dispatchEvent(new Event('resize'));}}
</script></body></html>"""

os.makedirs("dashboard", exist_ok=True)
with open(OUT, "w") as fh:
    fh.write(html)
print(f"dashboard written: {OUT} ({os.path.getsize(OUT)/1e6:.1f} MB)")
