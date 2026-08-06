# -*- coding: utf-8 -*-
"""
Генератор коммерческого предложения (.docx) по заказу (Order).

Идея: на вход подаётся объект Order. Сервис сам находит все связанные
с заказом изделия — Portal (порталы) и Glukhar (глухие окна) — и строит
docx-файл, повторяя блок "изделие" столько раз, сколько изделий каждого
типа есть в заказе (0..N штук каждого вида).

Зависимости: python-docx (пакет "python-docx" на PyPI, импортируется как `docx`).

    pip install python-docx

Как использовать в Django:

    from orders.models import Order
    from proposal_generator import build_commercial_proposal

    order = Order.objects.get(pk=order_id)
    buffer = build_commercial_proposal(order)  # BytesIO
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    response["Content-Disposition"] = f'attachment; filename="KP_{order.pk}.docx"'
    return response

--------------------------------------------------------------------------
ВАЖНО — места, которые нужно донастроить под реальный проект (см. пометки
"# НАСТРОЙКА:" по тексту):

1. get_product_price() — предполагает, что calculation_details у Portal
   хранит словарь вида {..., "portal_total_with_ratio": ..., ...}
   (как возвращает calculate_beams/calculate_portals), а у Glukhar —
   словарь вида result[name] из calculate_glukhar (с ключами
   "price_with_ratio", "ИТОГО" и т.д.). Если реальные ключи, под которыми
   вы сохраняете calculation_details, называются иначе — поправьте список
   PORTAL_PRICE_KEYS / GLUKHAR_PRICE_KEYS.

2. get_portal_image_path() / get_glukhar_image_path() — сейчас картинка
   подбирается по названию схемы (Scheme.name) / типа дерева (для
   глухаря) через словари SCHEME_IMAGE_MAP / GLUKHAR_IMAGE_MAP, с
   резервным изображением по умолчанию. Пропишите там реальные пути к
   файлам в static (STATIC_ROOT / STATICFILES_DIRS).

3. Шапка документа (компания, ИНН, ОГРН, срок отгрузки) — эти данные не
   хранятся в Order, поэтому вынесены в параметры build_commercial_proposal().

4. Текст "Тип стеклопакета" всегда "40мм закалённый" — как и попросили.
   Сторона ручки определяется по имени hardware_type: "Standard" →
   односторонняя, "Standard+" → двухсторонняя (см. HARDWARE_SIDE_MAP).
"""

from __future__ import annotations

import io
import os
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Iterable, Optional

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.enum.section import WD_SECTION


# --------------------------------------------------------------------------
# НАСТРОЙКА: пути к изображениям изделий.
#
# Ключ — Scheme.name (для порталов) / GlukharWood.name (для глухих окон).
# Значение — абсолютный путь к файлу картинки в статике проекта.
# Если для конкретной схемы/дерева картинки нет в словаре — используется
# DEFAULT_PORTAL_IMAGE / DEFAULT_GLUKHAR_IMAGE.
# --------------------------------------------------------------------------
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

DEFAULT_PORTAL_IMAGE = os.path.join(ASSETS_DIR, "portal_default.jpg")
DEFAULT_GLUKHAR_IMAGE = os.path.join(ASSETS_DIR, "glukhar_default.jpeg")
COMPANY_LOGO = os.path.join(ASSETS_DIR, "logo.png")

# Пример: "Схема А": "/path/to/static/portals/scheme_a.jpg"
SCHEME_IMAGE_MAP: dict[str, str] = {
    # "Схема А. HS-портал": os.path.join(ASSETS_DIR, "scheme_a.jpg"),
}

GLUKHAR_IMAGE_MAP: dict[str, str] = {
    # "Сосна": os.path.join(ASSETS_DIR, "glukhar_pine.jpg"),
}

# Сторона ручки по названию типа фурнитуры (Hardware.name)
HARDWARE_SIDE_MAP = {
    "Standard": "ручка односторонняя",
    "Standard+": "ручка двухсторонняя",
}

GLASS_TYPE_TEXT = "40мм закалённый"

# НАСТРОЙКА: под какими ключами в calculation_details лежит финальная
# цена изделия (с учётом коэффициента). Проверяются по порядку, первое
# найденное значение используется.
PORTAL_PRICE_KEYS = ("portal_total_with_ratio", "portal_total")
GLUKHAR_PRICE_KEYS = ("price_with_ratio",)  # запасной вариант ниже, через "ИТОГО"

FONT_NAME = "Times New Roman"

SCHEME_LETTERS = "АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЭЮЯ"


# --------------------------------------------------------------------------
# Вспомогательные функции
# --------------------------------------------------------------------------


def _to_decimal(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def _fmt_money(value) -> str:
    """1999999.5 -> '1 999 999,50 ₽'"""
    value = _to_decimal(value).quantize(Decimal("0.01"))
    sign, digits, exponent = value.as_tuple()
    int_part = str(abs(value.to_integral_value(rounding="ROUND_FLOOR")))
    frac = f"{abs(value):.2f}".split(".")[1]
    grouped = []
    while len(int_part) > 3:
        grouped.insert(0, int_part[-3:])
        int_part = int_part[:-3]
    grouped.insert(0, int_part)
    formatted = " ".join(grouped)
    prefix = "-" if value < 0 else ""
    return f"{prefix}{formatted},{frac} ₽"


def _fmt_area(value) -> str:
    value = _to_decimal(value).quantize(Decimal("0.01"))
    return f"{value}".replace(".", ",")


def get_product_price(product) -> Decimal:
    """
    Достаёт итоговую (с коэффициентом) стоимость ОДНОЙ штуки/партии изделия
    из уже посчитанного product.calculation_details.

    Поддерживает и форму, которую возвращает calculate_beams (для Portal),
    и форму result[name] из calculate_glukhar (для Glukhar).
    """
    details = getattr(product, "calculation_details", None) or {}
    if not isinstance(details, dict):
        return Decimal("0")

    for key in PORTAL_PRICE_KEYS:
        if key in details:
            return _to_decimal(details[key])

    for key in GLUKHAR_PRICE_KEYS:
        if key in details:
            return _to_decimal(details[key])

    itogo = details.get("ИТОГО")

    if isinstance(itogo, dict) and "N_price" in itogo:
        return _to_decimal(itogo["N_price"])

    if itogo is not None and not isinstance(itogo, dict):
        return _to_decimal(itogo)

    return Decimal("0")


def get_portal_image_path(portal) -> str:
    scheme_name = getattr(getattr(portal, "scheme", None), "name", None)
    return SCHEME_IMAGE_MAP.get(scheme_name, DEFAULT_PORTAL_IMAGE)


def get_glukhar_image_path(glukhar) -> str:
    wood_name = getattr(getattr(glukhar, "wood_type", None), "name", None)
    return GLUKHAR_IMAGE_MAP.get(wood_name, DEFAULT_GLUKHAR_IMAGE)


def get_hardware_side_text(portal) -> str:
    hardware_name = getattr(getattr(portal, "hardware_type", None), "name", None)
    return HARDWARE_SIDE_MAP.get(hardware_name, "ручка односторонняя")


def get_color_display(product) -> str:
    color = getattr(product, "color_type", None)
    return getattr(color, "name", "") or "-"


# --------------------------------------------------------------------------
# Низкоуровневые помощники для python-docx
# --------------------------------------------------------------------------


def _set_cell_shading(cell, hex_color: str) -> None:
    shd = cell._tc.get_or_add_tcPr().makeelement(qn("w:shd"), {})
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    cell._tc.get_or_add_tcPr().append(shd)


def _set_font(run, size=11, bold=False, color=None):
    run.font.name = FONT_NAME
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.append(rfonts)
    rfonts.set(qn("w:eastAsia"), FONT_NAME)


def _add_heading(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    _set_font(run, size=13, bold=True)


def _add_kv_table(doc: Document, rows: Iterable[tuple[str, str]]) -> None:
    """Двухколоночная таблица 'подпись | значение' (Материал/Фурнитура/Цвет/...)."""
    rows = list(rows)
    table = doc.add_table(rows=len(rows), cols=2)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    widths = (Cm(4.5), Cm(11.5))
    for i, (label, value) in enumerate(rows):
        row = table.rows[i]
        row.cells[0].width = widths[0]
        row.cells[1].width = widths[1]

        p0 = row.cells[0].paragraphs[0]
        r0 = p0.add_run(label)
        _set_font(r0, size=10, bold=True)

        p1 = row.cells[1].paragraphs[0]
        r1 = p1.add_run(str(value))
        _set_font(r1, size=10)
    doc.add_paragraph()


def _safe_image_stream(image_path: str) -> io.BytesIO:
    """
    python-docx's own JPEG-header parser иногда не распознаёт progressive
    JPEG (частый случай для картинок из static/CMS-выгрузок) и падает с
    UnrecognizedImageError, хотя файл абсолютно валиден. Прогоняем через
    Pillow и пересохраняем в надёжном baseline-формате перед вставкой.
    """
    from PIL import Image

    with Image.open(image_path) as im:
        im = im.convert("RGB") if im.mode not in ("RGB", "RGBA") else im
        buf = io.BytesIO()
        fmt = "PNG" if im.mode == "RGBA" else "JPEG"
        im.save(buf, format=fmt)
        buf.seek(0)
        return buf


def _add_product_block(
    doc: Document, image_path: str, spec_rows: Iterable[tuple[str, str]]
) -> None:
    """
    Таблица 'картинка | подпись | значение' — картинка изделия слева
    (объединена по вертикали на все строки), справа характеристики.
    """
    spec_rows = list(spec_rows)
    n_rows = len(spec_rows)

    table = doc.add_table(rows=n_rows, cols=3)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    col_widths = (Cm(6.0), Cm(6.0), Cm(4.0))
    for row in table.rows:
        for cell, w in zip(row.cells, col_widths):
            cell.width = w

    # Объединяем картиночную колонку по вертикали
    img_cell = table.cell(0, 0)
    if n_rows > 1:
        img_cell = img_cell.merge(table.cell(n_rows - 1, 0))
    img_cell.vertical_alignment = 1  # center
    img_para = img_cell.paragraphs[0]
    img_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = img_para.add_run()
    try:
        run.add_picture(_safe_image_stream(image_path), width=Cm(5.5))
    except Exception:
        # если файл картинки не найден/битый — не роняем генерацию документа
        placeholder = img_para.add_run("[изображение недоступно]")
        _set_font(placeholder, size=9)

    for i, (label, value) in enumerate(spec_rows):
        label_cell = table.cell(i, 1)
        value_cell = table.cell(i, 2)

        lp = label_cell.paragraphs[0]
        lr = lp.add_run(label)
        _set_font(lr, size=10)

        vp = value_cell.paragraphs[0]
        vr = vp.add_run(str(value))
        _set_font(vr, size=10, bold=True)

    doc.add_paragraph()


# --------------------------------------------------------------------------
# Сборка блоков "Портал" и "Глухарь"
# --------------------------------------------------------------------------


def _add_portal_section(doc: Document, portal, index: int) -> Decimal:
    scheme = portal.scheme
    letter = SCHEME_LETTERS[index % len(SCHEME_LETTERS)]
    _add_heading(doc, f"Схема {letter}. {scheme.name}.")

    width = portal.width
    height = portal.height
    amount = portal.amount
    area_total = (
        _to_decimal(width) * _to_decimal(height) / Decimal("1000000")
    ) * _to_decimal(amount)
    price = get_product_price(portal)

    spec_rows = [
        ("Высота проема, мм:", str(height)),
        ("Ширина проема, мм:", str(width)),
        ("Количество изделий, шт", str(amount)),
        ("Площадь изделий, м\u00b2", _fmt_area(area_total)),
        ("Стоимость изделий, рублей", _fmt_money(price)),
    ]
    _add_product_block(doc, get_portal_image_path(portal), spec_rows)

    wood_name = getattr(portal.wood_type, "name", "-")
    _add_kv_table(
        doc,
        [
            ("Материал", f"{wood_name}, клееный брус 78 мм"),
            ("Фурнитура", f"HS-Portal, {get_hardware_side_text(portal)}"),
            ("Цвет", get_color_display(portal)),
            ("Тип стеклопакета", GLASS_TYPE_TEXT),
        ],
    )
    return price


def _add_glukhar_section(doc: Document, glukhar, index: int) -> Decimal:
    _add_heading(doc, "Глухое окно" if index == 0 else f"Глухое окно ({index + 1})")

    width = glukhar.width
    height = glukhar.height
    amount = glukhar.amount
    area_total = (
        _to_decimal(width) * _to_decimal(height) / Decimal("1000000")
    ) * _to_decimal(amount)
    price = get_product_price(glukhar)

    spec_rows = [
        ("Высота проема, мм:", str(height)),
        ("Ширина проема, мм:", str(width)),
        ("Количество изделий, шт", str(amount)),
        ("Площадь изделий, м\u00b2", _fmt_area(area_total)),
        ("Стоимость изделий, рублей", _fmt_money(price)),
    ]
    _add_product_block(doc, get_glukhar_image_path(glukhar), spec_rows)

    wood_name = getattr(glukhar.wood_type, "name", "-")
    _add_kv_table(
        doc,
        [
            ("Материал", f"{wood_name}, клееный брус"),
            ("Цвет", get_color_display(glukhar)),
            ("Тип стеклопакета", GLASS_TYPE_TEXT),
        ],
    )
    return price


# --------------------------------------------------------------------------
# Шапка и итоговый блок
# --------------------------------------------------------------------------


def _add_document_header(
    doc: Document,
    company_name: str,
    inn: str,
    ogrn: str,
    proposal_date: str,
    shipment_term: str,
) -> None:
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    table.columns[0].width = Cm(12.0)
    table.columns[1].width = Cm(4.0)

    left_cell = table.cell(0, 0)
    p = left_cell.paragraphs[0]
    r = p.add_run("КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ")
    _set_font(r, size=16, bold=True)

    p2 = left_cell.add_paragraph()
    r2 = p2.add_run(company_name)
    _set_font(r2, size=10)

    p3 = left_cell.add_paragraph()
    r3 = p3.add_run(f"ИНН {inn}")
    _set_font(r3, size=10)

    p4 = left_cell.add_paragraph()
    r4 = p4.add_run(f"ОГРН {ogrn}")
    _set_font(r4, size=10)

    right_cell = table.cell(0, 1)
    rp = right_cell.paragraphs[0]
    rp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    rrun = rp.add_run()
    if os.path.exists(COMPANY_LOGO):
        try:
            rrun.add_picture(COMPANY_LOGO, width=Cm(2.6))
        except Exception:
            pass

    doc.add_paragraph()

    meta_table = doc.add_table(rows=2, cols=2)
    meta_table.style = "Table Grid"
    meta_rows = [("Дата КП:", proposal_date), ("Срок отгрузки:", shipment_term)]
    for i, (label, value) in enumerate(meta_rows):
        c0, c1 = meta_table.rows[i].cells
        r0 = c0.paragraphs[0].add_run(label)
        _set_font(r0, size=10, bold=True)
        r1 = c1.paragraphs[0].add_run(value)
        _set_font(r1, size=10)

    doc.add_paragraph()


def _add_totals_block(
    doc: Document,
    items_total: Decimal,
    items_count: int,
    installation: Decimal,
    delivery: Decimal,
    unloading: Decimal,
    grand_total: Decimal,
) -> None:
    _add_heading(doc, "Стоимость заказа:")

    table = doc.add_table(rows=4, cols=2)
    table.style = "Table Grid"
    rows = [
        (f"Стоимость изделий, {items_count} шт", _fmt_money(items_total)),
        ("Монтаж", _fmt_money(installation)),
        ("Доставка", _fmt_money(delivery)),
        ("Разгрузка", _fmt_money(unloading)),
    ]
    for i, (label, value) in enumerate(rows):
        c0, c1 = table.rows[i].cells
        r0 = c0.paragraphs[0].add_run(label)
        _set_font(r0, size=10)
        r1 = c1.paragraphs[0].add_run(value)
        _set_font(r1, size=10, bold=True)

    doc.add_paragraph()

    total_table = doc.add_table(rows=1, cols=2)
    total_table.style = "Table Grid"
    c0, c1 = total_table.rows[0].cells
    r0 = c0.paragraphs[0].add_run("Итого:")
    _set_font(r0, size=12, bold=True)
    r1 = c1.paragraphs[0].add_run(_fmt_money(grand_total))
    _set_font(r1, size=12, bold=True)

    doc.add_paragraph()

    _add_heading(doc, "График платежей:")
    pay_table = doc.add_table(rows=2, cols=2)
    pay_table.style = "Table Grid"
    first_payment = (grand_total * Decimal("0.7")).quantize(Decimal("0.01"))
    second_payment = (grand_total - first_payment).quantize(Decimal("0.01"))
    pay_rows = [
        ("Первый платеж, 70% (предоплата)", _fmt_money(first_payment)),
        ("Второй платеж, 30% (по готовности изделий)", _fmt_money(second_payment)),
    ]
    for i, (label, value) in enumerate(pay_rows):
        c0, c1 = pay_table.rows[i].cells
        r0 = c0.paragraphs[0].add_run(label)
        _set_font(r0, size=10)
        r1 = c1.paragraphs[0].add_run(value)
        _set_font(r1, size=10, bold=True)


# --------------------------------------------------------------------------
# Точка входа
# --------------------------------------------------------------------------


def build_commercial_proposal(
    order,
    *,
    company_name: str = "Индивидуальный предприниматель Дубров Игорь Викторович",
    inn: str = "000000000",
    ogrn: str = "0000000000",
    proposal_date: Optional[str] = None,
    shipment_term: str = "",
) -> io.BytesIO:
    """
    Строит .docx коммерческого предложения по заказу `order` (экземпляр
    orders.models.Order) и возвращает BytesIO с готовым файлом.

    Изделия заказа находятся сами — через related-менеджеры
    order.portal_set (calculate.models.Portal) и order.glukhar_set
    (calculate.models.Glukhar). Каждая строка Portal/Glukhar формирует
    свой блок в документе; поле `amount` этой строки — это количество
    одинаковых изделий данного типа/размера в заказе.
    """
    if proposal_date is None:
        # НАСТРОЙКА: если нужна другая дата (например order.created_at),
        # передайте её явно через параметр proposal_date.
        from datetime import date

        proposal_date = date.today().strftime("%d.%m.%y")

    doc = Document()
    section = doc.sections[0]
    section.left_margin = Cm(1.5)
    section.right_margin = Cm(1.5)

    _add_document_header(doc, company_name, inn, ogrn, proposal_date, shipment_term)

    portals = list(
        order.portal_set.select_related(
            "scheme", "wood_type", "hardware_type", "color_type"
        ).all()
    )
    glukhars = list(order.glukhar_set.select_related("wood_type", "color_type").all())

    items_total = Decimal("0")
    items_count = 0

    for i, portal in enumerate(portals):
        items_total += get_product_price(portal)
        items_count += portal.amount
        _add_portal_section(doc, portal, i)

    for i, glukhar in enumerate(glukhars):
        items_total += get_product_price(glukhar)
        items_count += glukhar.amount
        _add_glukhar_section(doc, glukhar, i)

    installation = _to_decimal(order.installation)
    delivery = _to_decimal(order.delivery)
    unloading = _to_decimal(order.unloading)

    # НАСТРОЙКА: если хотите пересчитывать итог сами (а не брать
    # готовое order.total_sum), раскомментируйте строку ниже и
    # примените вашу логику скидки (order.discount).
    # grand_total = items_total + installation + delivery + unloading
    grand_total = _to_decimal(order.total_sum) or (
        items_total + installation + delivery + unloading
    )

    _add_totals_block(
        doc,
        items_total=items_total,
        items_count=items_count,
        installation=installation,
        delivery=delivery,
        unloading=unloading,
        grand_total=grand_total,
    )

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
