"""Natija sertifikati (PDF, A4 albom). Dizayn TZ 6-band tokenlari asosida."""

import io
import json
import math
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.utils import timezone
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import simpleSplit
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

BASE = Path(__file__).resolve().parent
FONTS = BASE / "fonts"

INK = HexColor("#1B2A41")
ACCENT = HexColor("#E4572E")
TEAL = HexColor("#2A7F8F")
SOFT = HexColor("#9AB3C2")
PANEL = HexColor("#F4F1EA")
PAGE = HexColor("#FBFAF7")
LINE = HexColor("#D6D0C4")
MUTED = HexColor("#7A8291")
WHITE = HexColor("#FFFFFF")


@lru_cache(maxsize=1)
def register_fonts():
    for name, file in [
        ("Inter", "Inter-Regular.ttf"),
        ("Inter-Medium", "Inter-Medium.ttf"),
        ("Inter-SemiBold", "Inter-SemiBold.ttf"),
        ("Inter-Bold", "Inter-Bold.ttf"),
    ]:
        pdfmetrics.registerFont(TTFont(name, str(FONTS / file)))
    return True


@lru_cache(maxsize=2)
def texts(lang):
    with open(BASE / "i18n" / f"{lang}.json", encoding="utf-8") as fh:
        return json.load(fh)


def format_date(dt, lang):
    t = texts(lang)
    dt = timezone.localtime(dt)
    return t["date_format"].format(day=dt.day, month=t["months"][dt.month - 1], year=dt.year)


def star(c, cx, cy, r_out, r_in, points, rotation=-90):
    path = c.beginPath()
    for i in range(points * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rotation + i * 180 / points)
        x, y = cx + r * math.cos(a), cy - r * math.sin(a)
        if i == 0:
            path.moveTo(x, y)
        else:
            path.lineTo(x, y)
    path.close()
    return path


def triangle(c, cx, cy, size):
    h = size * math.sqrt(3) / 2
    path = c.beginPath()
    path.moveTo(cx, cy + h * 2 / 3)
    path.lineTo(cx - size / 2, cy - h / 3)
    path.lineTo(cx + size / 2, cy - h / 3)
    path.close()
    return path


def fit_font_size(text, font, max_size, max_width, min_size=18):
    size = max_size
    while size > min_size and pdfmetrics.stringWidth(text, font, size) > max_width:
        size -= 1
    return size


def draw_decorations(c, w, h):
    # Yuqori-o‘ngdagi yulduzlar
    c.setFillColor(INK)
    c.drawPath(star(c, w - 120, h - 92, 20, 8, 4), stroke=0, fill=1)
    c.setFillColor(SOFT)
    c.drawPath(star(c, w - 78, h - 120, 13, 6, 5), stroke=0, fill=1)
    c.setFillColor(TEAL)
    c.drawPath(triangle(c, w - 156, h - 136, 22), stroke=0, fill=1)

    # O‘ng tomonda yumshoq aylana
    c.setStrokeColor(SOFT)
    c.setLineWidth(1.5)
    c.circle(w - 112, h / 2 - 10, 26, stroke=1, fill=0)
    c.setFillColor(ACCENT)
    c.circle(w - 112, h / 2 - 10, 6, stroke=0, fill=1)


def verify_url(result):
    code = (result.get("verify_code") or "").replace("-", "")
    return f"{settings.PUBLIC_URL}/verify/{code}"


def draw_qr(c, result, t, w):
    """O‘ng pastda QR kod: skaner qilinganda serverdagi haqiqiy ma’lumot ochiladi."""
    size = 92
    x, y = w - 64 - size, 66
    widget = QrCodeWidget(verify_url(result), barLevel="M")
    x0, y0, x1, y1 = widget.getBounds()
    drawing = Drawing(size, size, transform=[size / (x1 - x0), 0, 0, size / (y1 - y0), 0, 0])
    widget.barFillColor = INK
    drawing.add(widget)
    c.setFillColor(WHITE)
    c.setStrokeColor(LINE)
    c.roundRect(x - 6, y - 6, size + 12, size + 12, 10, stroke=1, fill=1)
    renderPDF.draw(drawing, c, x, y)
    # Izoh QR ustida, o‘ng chetga tekislangan
    c.setFillColor(MUTED)
    c.setFont("Inter-Medium", 7.5)
    lines = simpleSplit(t["scan_to_verify"], "Inter-Medium", 7.5, size + 12)
    for i, line in enumerate(reversed(lines)):
        c.drawRightString(x + size + 6, y + size + 14 + i * 10, line)


def render_certificate(result, lang="uz"):
    register_fonts()
    t = texts(lang)
    w, h = landscape(A4)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(w, h))
    c.setTitle(f"{t['title']} — {result['full_name']}")
    c.setAuthor(t["brand"])

    # Fon va panel
    c.setFillColor(PAGE)
    c.rect(0, 0, w, h, stroke=0, fill=1)
    margin = 28
    c.setFillColor(PANEL)
    c.setStrokeColor(LINE)
    c.setLineWidth(1)
    c.roundRect(margin, margin, w - 2 * margin, h - 2 * margin, 18, stroke=1, fill=1)
    c.setFillColor(WHITE)
    c.roundRect(margin + 14, margin + 14, w - 2 * margin - 28, h - 2 * margin - 28, 14, stroke=1, fill=1)

    draw_decorations(c, w, h)

    left = 84
    # Brend
    c.setFillColor(INK)
    c.roundRect(left, h - 104, 26, 26, 7, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont("Inter-Bold", 15)
    c.drawCentredString(left + 13, h - 96, "?")
    c.setFillColor(INK)
    c.setFont("Inter-SemiBold", 10.5)
    c.drawString(left + 36, h - 95, t["brand"])

    # Sarlavha
    c.setFont("Inter-Bold", 40)
    c.drawString(left, h - 160, t["title"])
    c.setFillColor(MUTED)
    c.setFont("Inter", 13)
    c.drawString(left, h - 184, t["subtitle"])

    # Ism
    c.setFont("Inter-Medium", 11)
    c.drawString(left, h - 232, t["awarded_to"].upper())
    name = result["full_name"]
    size = fit_font_size(name, "Inter-Bold", 34, w - left - 220)
    c.setFillColor(INK)
    c.setFont("Inter-Bold", size)
    c.drawString(left, h - 274, name)
    c.setStrokeColor(LINE)
    c.line(left, h - 290, w - 220, h - 290)

    # Ko‘rsatkichlar
    level = result.get("level") or {}
    level_name = level.get(f"name_{lang}") or "—"
    stats = [
        (t["score"], f"{result['total_score'] or 0} / {result['max_score']}"),
        (t["percent"], f"{result['percent']:.0f}%"),
        (t["level"], level_name),
    ]
    box_w, box_h, gap = 170, 66, 14
    y = h - 376
    for i, (label, value) in enumerate(stats):
        x = left + i * (box_w + gap)
        highlight = i == 2
        c.setFillColor(ACCENT if highlight else PANEL)
        c.setStrokeColor(ACCENT if highlight else LINE)
        c.roundRect(x, y, box_w, box_h, 14, stroke=1, fill=1)
        c.setFillColor(WHITE if highlight else MUTED)
        c.setFont("Inter-Medium", 9.5)
        c.drawString(x + 16, y + box_h - 21, label.upper())
        c.setFillColor(WHITE if highlight else INK)
        vsize = fit_font_size(value, "Inter-Bold", 24, box_w - 32, min_size=12)
        c.setFont("Inter-Bold", vsize)
        c.drawString(x + 16, y + 16, value)

    # Kategoriyalar: uchta ustun, har birida nom, foiz va chiziq
    cats = result.get("categories") or []
    if cats:
        row_w = 3 * box_w + 2 * gap
        col_gap = 22
        col_w = (row_w - col_gap * (len(cats) - 1)) / len(cats)
        cy = y - 52
        for i, cat in enumerate(cats):
            x = left + i * (col_w + col_gap)
            c.setFillColor(INK)
            label = cat[f"name_{lang}"]
            c.setFont("Inter-Medium", fit_font_size(label, "Inter-Medium", 9.5, col_w - 34, min_size=7))
            c.drawString(x, cy + 10, label)
            c.setFont("Inter-SemiBold", 9.5)
            c.drawRightString(x + col_w, cy + 10, f"{cat['percent']:.0f}%")
            c.setFillColor(PANEL)
            c.roundRect(x, cy, col_w, 4, 2, stroke=0, fill=1)
            c.setFillColor(TEAL)
            c.roundRect(x, cy, max(4, col_w * cat["percent"] / 100), 4, 2, stroke=0, fill=1)

    # Pastki qism
    finished = result.get("finished_at") or timezone.now()
    c.setFillColor(MUTED)
    c.setFont("Inter-Medium", 9.5)
    c.drawString(left, 104, t["date"].upper())
    c.drawString(left + 200, 104, t["answered"].upper())
    c.drawString(left + 400, 104, t["certificate_id"].upper())
    c.setFillColor(INK)
    c.setFont("Inter-SemiBold", 13)
    c.drawString(left, 84, format_date(finished, lang))
    c.drawString(left + 200, 84, f"{result['answered_count']} / {result['total_questions']}")
    c.drawString(left + 400, 84, result.get("verify_code") or result["attempt_id"][:8].upper())
    draw_qr(c, result, t, w)

    c.setFillColor(MUTED)
    c.setFont("Inter", 8.5)
    c.drawString(left, 58, t["footer"].format(count=result["total_questions"]))

    c.showPage()
    c.save()
    return buf.getvalue()
