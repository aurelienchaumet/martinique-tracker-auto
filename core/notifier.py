import html
import io
import smtplib
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import GMAIL_APP_PASSWORD, GMAIL_USER, RECIPIENT_EMAIL, ROUTES
from core.alert_engine import Alert
from core.price_store import PriceRecord


def build_subject(alert: Alert) -> str:
    kind = "CHUTE" if alert.is_drop else "HAUSSE"
    return (
        f"✈️ [{kind} {alert.label}] {alert.airline} "
        f"{alert.outbound} → {alert.return_date}"
    )


def build_email_html(alerts: List[Alert]) -> str:
    rows = ""
    for a in alerts:
        color = "#2e7d32" if a.is_drop else "#c62828"
        rows += f"""
        <tr>
          <td>{html.escape(a.airline)}</td>
          <td>{a.outbound}</td>
          <td>{a.return_date}</td>
          <td>{a.old_price:.0f}€</td>
          <td style="color:{color};font-weight:bold">{a.new_price:.0f}€</td>
          <td style="color:{color}">{a.label}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:sans-serif">
  <h2>✈️ Alerte prix — Martinique</h2>
  <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse">
    <thead style="background:#1565c0;color:white">
      <tr>
        <th>Compagnie</th><th>Aller</th><th>Retour</th>
        <th>Ancien prix</th><th>Nouveau prix</th><th>Variation</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
  <p style="color:#888;font-size:12px">
    Mis à jour le {datetime.now().strftime("%d/%m/%Y %H:%M")}
  </p>
</body>
</html>"""


def generate_pdf_bytes(records: List[PriceRecord]) -> bytes:
    combos = [(r["outbound"], r["return"]) for r in ROUTES]
    airlines = sorted({r.airline for r in records})

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Évolution des prix ORY → FDF", fontsize=14, fontweight="bold")

    for idx, (outbound, ret) in enumerate(combos):
        ax = axes[idx // 2][idx % 2]
        ax.set_title(f"{outbound} → {ret}", fontsize=10)
        ax.set_xlabel("Date")
        ax.set_ylabel("Prix (€)")

        for airline in airlines:
            pts = [
                (r.timestamp, r.price)
                for r in records
                if r.airline == airline
                and r.outbound == outbound
                and r.return_date == ret
            ]
            if pts:
                times, prices = zip(*pts)
                ax.plot(times, prices, marker="o", label=airline, markersize=3)

        ax.legend(fontsize=8)
        ax.tick_params(axis="x", rotation=45, labelsize=7)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="pdf")
    plt.close(fig)
    return buf.getvalue()


def send_alert_email(alerts: List[Alert], records: List[PriceRecord]) -> None:
    if not alerts:
        return

    if not GMAIL_USER or not GMAIL_APP_PASSWORD or not RECIPIENT_EMAIL:
        print("[notifier] No GMAIL credentials — skipping email.")
        return

    subject = build_subject(alerts[0]) if len(alerts) == 1 else "✈️ Alertes prix Martinique"
    html = build_email_html(alerts)
    pdf = generate_pdf_bytes(records)

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = RECIPIENT_EMAIL
    msg.attach(MIMEText(html, "html", "utf-8"))

    attachment = MIMEApplication(pdf, _subtype="pdf")
    filename = f"martinique_prix_{datetime.now().strftime('%Y-%m-%d_%H')}.pdf"
    attachment.add_header("Content-Disposition", "attachment", filename=filename)
    msg.attach(attachment)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, RECIPIENT_EMAIL, msg.as_string())

    print(f"[notifier] Email sent: {subject}")
