import html
import json
from datetime import datetime
from pathlib import Path
from typing import List

from config import ROUTES
from core.price_store import PriceRecord

OUTPUT_PATH = Path(__file__).parent / "index.html"


def generate_dashboard(records: List[PriceRecord]) -> str:
    airlines = sorted({r.airline for r in records})
    colors = ["#1565c0", "#2e7d32", "#c62828", "#6a1b9a"]
    airline_colors = {a: colors[i % len(colors)] for i, a in enumerate(airlines)}

    charts_js = ""
    cards_html = ""

    for route in ROUTES:
        outbound = route["outbound"]
        ret = route["return"]
        combo_id = f"{outbound}_{ret}".replace("-", "")
        combo_label = f"{outbound} → {ret}"

        datasets = []
        for airline in airlines:
            pts = sorted(
                [r for r in records if r.airline == airline and r.outbound == outbound and r.return_date == ret],
                key=lambda r: r.timestamp,
            )
            if pts:
                labels = [r.timestamp[:16] for r in pts]
                prices = [r.price for r in pts]
                datasets.append({
                    "label": airline,
                    "data": prices,
                    "labels": labels,
                    "borderColor": airline_colors[airline],
                    "backgroundColor": airline_colors[airline] + "22",
                    "fill": False,
                    "tension": 0.3,
                })

        all_pts = [r for r in records if r.outbound == outbound and r.return_date == ret]
        current_by_airline = {}
        for airline in airlines:
            a_pts = [r for r in all_pts if r.airline == airline]
            if a_pts:
                current_by_airline[airline] = sorted(a_pts, key=lambda r: r.timestamp)[-1].price

        min_price = min((r.price for r in all_pts), default=0)
        max_price = max((r.price for r in all_pts), default=0)

        table_rows = ""
        for airline, price in current_by_airline.items():
            diff = price - min_price
            indicator = "🟢" if diff < 20 else ("🔴" if price >= max_price - 20 else "🟡")
            table_rows += f"<tr><td>{html.escape(airline)}</td><td><b>{price:.0f}€</b></td><td>{indicator}</td></tr>"

        all_labels = sorted({r.timestamp[:16] for r in all_pts})
        chart_datasets = json.dumps(datasets).replace("</", "<\\/")

        charts_js += f"""
        (function() {{
            var ctx = document.getElementById('chart_{combo_id}').getContext('2d');
            var raw = {chart_datasets};
            var labels = {json.dumps(all_labels)};
            var datasets = raw.map(function(d) {{
                return {{
                    label: d.label,
                    data: labels.map(function(l) {{
                        var i = d.labels.indexOf(l);
                        return i >= 0 ? d.data[i] : null;
                    }}),
                    borderColor: d.borderColor,
                    backgroundColor: d.backgroundColor,
                    fill: d.fill,
                    tension: d.tension,
                    spanGaps: true,
                }};
            }});
            new Chart(ctx, {{
                type: 'line',
                data: {{ labels: labels, datasets: datasets }},
                options: {{
                    responsive: true,
                    plugins: {{ legend: {{ position: 'top' }} }},
                    scales: {{ y: {{ title: {{ display: true, text: 'Prix (€)' }} }} }}
                }}
            }});
        }})();
"""

        cards_html += f"""
        <div class="card">
            <h3>✈️ {combo_label}</h3>
            <canvas id="chart_{combo_id}" height="120"></canvas>
            <table>
                <thead><tr><th>Compagnie</th><th>Prix actuel</th><th>Statut</th></tr></thead>
                <tbody>{table_rows}</tbody>
            </table>
            <p class="meta">Min historique : {min_price:.0f}€ &nbsp;|&nbsp; Max : {max_price:.0f}€</p>
        </div>"""

    updated_at = datetime.now().strftime("%d/%m/%Y %H:%M")

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>✈️ Prix Martinique</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    body {{ font-family: system-ui, sans-serif; background: #f5f5f5; margin: 0; padding: 16px; }}
    h1 {{ text-align: center; color: #1565c0; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; max-width: 1200px; margin: auto; }}
    @media (max-width: 768px) {{ .grid {{ grid-template-columns: 1fr; }} }}
    .card {{ background: white; border-radius: 8px; padding: 16px; box-shadow: 0 2px 4px rgba(0,0,0,.1); }}
    h3 {{ margin-top: 0; color: #1565c0; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
    th {{ background: #1565c0; color: white; padding: 6px 8px; text-align: left; }}
    td {{ padding: 6px 8px; border-bottom: 1px solid #eee; }}
    .meta {{ color: #888; font-size: 12px; margin-top: 8px; }}
    .updated {{ text-align: center; color: #888; font-size: 13px; margin-top: 24px; }}
  </style>
</head>
<body>
  <h1>✈️ Suivi des prix Paris Orly → Martinique</h1>
  <div class="grid">{cards_html}</div>
  <p class="updated">Mis à jour le {updated_at}</p>
  <script>{charts_js}</script>
</body>
</html>"""


def write_dashboard(records: List[PriceRecord]) -> None:
    html = generate_dashboard(records)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"[dashboard] Written to {OUTPUT_PATH}")
