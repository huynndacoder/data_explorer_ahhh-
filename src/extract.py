import re
import email
import pdfplumber
import os
from email.header import decode_header
from email.utils import parsedate_to_datetime
import urllib.parse


# ── helpers ─────────────────────────────────────────────────────────────────

def decode_mime_string(s):
    if not s:
        return None
    parts = decode_header(s)
    result = ""
    for part, enc in parts:
        if isinstance(part, bytes):
            result += part.decode(enc or "utf-8", errors="ignore")
        else:
            result += part
    return result.strip()


def _decode_payload_text(part):
    payload = part.get_payload(decode=True)
    if not payload:
        return ""
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except (LookupError, UnicodeDecodeError):
        return payload.decode("utf-8", errors="replace")


def _get_attachment_filename(part):
    """Robustly decode attachment filenames (MIME encoded-word + RFC 5987)."""
    raw = part.get_filename()
    if raw:
        # decode_header handles =?UTF-8?B?...?= and =?UTF-8?Q?...?= forms
        decoded_parts = decode_header(raw)
        result = ""
        for segment, enc in decoded_parts:
            if isinstance(segment, bytes):
                result += segment.decode(enc or "utf-8", errors="ignore")
            else:
                result += segment
        return result.strip() if result else None

    # Fallback: parse Content-Disposition manually for filename*=UTF-8''...
    cd = str(part.get("Content-Disposition") or "")
    match = re.search(
        r"filename\*=(?:UTF-8''|utf-8'')(.+?)(?:\s*;|$)", cd, re.IGNORECASE
    )
    if match:
        return urllib.parse.unquote(match.group(1).strip())
    return None


def _normalize_so_number(raw: str) -> str:
    """BH26_0935 → BH26.0935, BH26.0935 stays as-is."""
    return raw.replace("_", ".")


# ── main email parser ────────────────────────────────────────────────────────

def parse_email_and_extract_pdf(eml_file_path: str, temp_pdf_dir: str) -> tuple:
    """
    Parse an .eml file and save its PDF attachment to temp_pdf_dir.

    Returns:
        (email_data dict, pdf_path str or None)

    email_data keys:
        message_id, from_address, subject, received_at,
        attachment_name,
        anchor_so_number   — from subject / body / filename (dedup key)
        anchor_customer_code     — MST/tax_code from email body
        anchor_customer_name     — customer/dealer name from email body, used for customer auto-create
        anchor_customer_address  — address from email body, province_id still postponed
        anchor_total_amount      — total order value from email body, used for validation
    """
    with open(eml_file_path, "rb") as f:
        msg = email.message_from_binary_file(f)

    email_data = {
        "message_id": (msg.get("Message-ID") or "").strip(),
        "from_address": decode_mime_string(msg.get("From")),
        "subject": decode_mime_string(msg.get("Subject")),
        "received_at": None,
        "attachment_name": None,
        "anchor_so_number": None,
        "anchor_customer_code": None,
        "anchor_total_amount": 0,
    }

    date_str = msg.get("Date")
    if date_str:
        try:
            email_data["received_at"] = parsedate_to_datetime(date_str)
        except Exception:
            pass

    body_text = ""
    pdf_path = None

    for part in msg.walk():
        content_type = part.get_content_type()
        cd = str(part.get("Content-Disposition") or "")

        if content_type == "text/plain" and "attachment" not in cd:
            body_text += _decode_payload_text(part)
            continue

        if "attachment" in cd or content_type == "application/pdf":
            filename = _get_attachment_filename(part)
            if filename and filename.lower().endswith(".pdf"):
                safe_filename = os.path.basename(filename)
                pdf_path = os.path.join(temp_pdf_dir, safe_filename)
                payload = part.get_payload(decode=True)
                if payload:
                    with open(pdf_path, "wb") as pdf_file:
                        pdf_file.write(payload)
                email_data["attachment_name"] = safe_filename

    print("[DEBUG_EMAIL_BODY]", body_text[:500])

    # Anchors extracted from email body / subject (used to cross-check PDF)
    email_data["anchor_so_number"] = _extract_so_number(
        email_data["subject"], body_text, eml_file_path
    )
    email_data["anchor_customer_code"] = _extract_customer_code(body_text)
    email_data["anchor_customer_name"] = _extract_customer_name(body_text)
    email_data["anchor_customer_address"] = _extract_customer_address(body_text)
    email_data["anchor_total_amount"] = _extract_total_amount(body_text)

    return email_data, pdf_path


# ── so_number / customer_code / total_amount from email body ─────────────────

def _extract_so_number(subject, body, filename_hint=""):
    pattern = r"BH\d{2}[._]\d{4,5}"
    for text in (subject, body, os.path.basename(filename_hint)):
        if not text:
            continue
        m = re.search(pattern, text)
        if m:
            return _normalize_so_number(m.group(0))
    return None


def _extract_customer_code(body):
    """Extract MST (tax code) — used to resolve customer.customer_code."""
    for pattern in (
        r"MST\s*[:\-]?\s*(\d{10,13})",
        r"mã\s+số\s+thuế\s*[:\-]?\s*(\d{5,15})",
        r"tax\s+code\s*[:\-]?\s*(\d{5,15})",
        r"MST\s*[:\-]?\s*(\d{5,15})",
    ):
        m = re.search(pattern, body, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None

def _extract_customer_name(body: str) -> str | None:
    """
    Extract customer/dealer name from email body.
    Example:
        Đại lý : CÔNG TY CỔ PHẦN NAM TIẾN
        Tên : CÔNG TY TNHH PHÚC AN
        Khách hàng : CỬA HÀNG XE ĐẠP XUÂN MAI
    """
    patterns = (
        r"(?im)^\s*Đại\s*lý\s*[:\-]\s*([^\r\n]+)",
        r"(?im)^\s*Dai\s*ly\s*[:\-]\s*([^\r\n]+)",
        r"(?im)^\s*Customer\s*[:\-]\s*([^\r\n]+)",
        r"(?im)^\s*Khách\s*hàng\s*[:\-]\s*([^\r\n]+)",
        r"(?im)^\s*Khach\s*hang\s*[:\-]\s*([^\r\n]+)",
        r"(?im)^\s*Tên\s*[:\-]\s*([^\r\n]+)",
        r"(?im)^\s*Ten\s*[:\-]\s*([^\r\n]+)",
    )

    for pattern in patterns:
        m = re.search(pattern, body, re.IGNORECASE)
        if m:
            value = m.group(1).strip()
            return _clean_single_line(value)

    return None


def _extract_customer_address(body: str) -> str | None:
    """
    Extract customer/dealer address from email body.
    Example:
        Địa chỉ : Phường Phú Diễn, TP Hà Nội
    """
    patterns = (
        r"Địa\s*chỉ\s*[:\-]?\s*(.+)",
        r"Dia\s*chi\s*[:\-]?\s*(.+)",
        r"Address\s*[:\-]?\s*(.+)",
    )

    for pattern in patterns:
        m = re.search(pattern, body, re.IGNORECASE)
        if m:
            value = m.group(1).strip()
            return _clean_single_line(value)

    return None


def _clean_single_line(value: str | None) -> str | None:
    if not value:
        return None

    value = value.strip()
    value = value.splitlines()[0].strip()
    value = re.sub(r"\s+", " ", value)

    label_pattern = (
        r"^(Tên|Ten|Đại\s*lý|Dai\s*ly|Khách\s*hàng|Khach\s*hang|Customer)"
        r"\s*[:\-]\s*"
    )

    while re.match(label_pattern, value, flags=re.IGNORECASE):
        value = re.sub(label_pattern, "", value, flags=re.IGNORECASE).strip()

    return value or None


def _extract_total_amount(body):
    """Extract declared total from email body. Returns int (VND) or 0."""
    patterns = [
        # "trị giá X đồng" / "tổng X đồng"
        r"(?:trị\s*giá|tổng(?:\s+giá\s+trị)?)\s*[:\-]?\s*([\d.,]+)\s*(?:đồng|vnđ|vnd)",
        # plain number before đồng at sentence end
        r"([\d.,]{5,})\s*(?:đồng|vnđ)(?:\s*[.\n]|$)",
    ]
    for pat in patterns:
        m = re.search(pat, body, re.IGNORECASE)
        if m:
            raw = m.group(1).replace(".", "").replace(",", "")
            try:
                return int(raw)
            except ValueError:
                continue
    return 0


# ── PDF order-line extractor ─────────────────────────────────────────────────

# Expected column headers (Vietnamese) that appear in the PDF table
_HEADER_KEYWORDS = {
    "stt":        ["stt", "số", "tt"],
    "ma_hang":    ["mã hàng", "ma hang", "product code", "mã"],
    "ten_sp":     ["tên sản phẩm", "ten san pham", "product name", "tên"],
    "dvt":        ["đvt", "dvt", "đơn vị", "unit"],
    "sl":         ["sl", "số lượng", "quantity", "số lg"],
    "don_gia":    ["đơn giá", "don gia", "unit price", "đơn giá (đ)"],
    "thanh_tien": ["thành tiền", "thanh tien", "line total", "thành tiền (đ)", "tổng tiền"],
}


def _detect_column_indices(header_row: list) -> dict:
    """
    Given a raw header row from pdfplumber, return a dict
    mapping logical column name → column index.
    Returns {} if the row doesn't look like a header.
    """
    mapping = {}
    normalized = [
        str(cell).lower().replace("\n", " ").strip() if cell else ""
        for cell in header_row
    ]
    for col_name, keywords in _HEADER_KEYWORDS.items():
        for idx, cell_text in enumerate(normalized):
            if any(kw in cell_text for kw in keywords):
                if col_name not in mapping:  # take first match
                    mapping[col_name] = idx
                break
    return mapping


def _parse_int(s: str) -> int:
    """'1.898.148' or '1,898,148' → 1898148"""
    return int(str(s).replace(".", "").replace(",", "").strip())


def _extract_header_fields_from_pdf(pdf) -> dict:
    """
    Extract structured header fields from the first page of the PDF:
      so_number, order_date, customer_code, customer_name, address
    These are in the info table at the top (above the line-item table).
    Returns a dict with None for any field not found.
    """
    result = {
        "pdf_so_number": None,
        "pdf_order_date": None,
        "pdf_customer_name": None,
        "pdf_customer_code": None,
    }
    if not pdf.pages:
        return result

    text = pdf.pages[0].extract_text() or ""

    # so_number: "Số đơn hàng: BH26.0935" or "BH26.0935" anywhere
    m = re.search(r"(BH\d{2}[._]\d{4,5})", text)
    if m:
        result["pdf_so_number"] = _normalize_so_number(m.group(1))

    # order_date: DD/MM/YYYY
    m = re.search(r"(\d{2}/\d{2}/\d{4})", text)
    if m:
        result["pdf_order_date"] = m.group(1)  # keep as string; parse in loader

    # customer name: line after "Đại lý" label
    m = re.search(r"(?:Đại\s*lý|dai\s*ly)\s*[:\-]?\s*(.+)", text, re.IGNORECASE)
    if m:
        result["pdf_customer_name"] = m.group(1).strip()

    # customer code (MST) in PDF
    m = re.search(r"MST\s*[:\-]?\s*(\d{5,15})", text, re.IGNORECASE)
    if m:
        result["pdf_customer_code"] = m.group(1).strip()

    return result


def process_pdf_order(pdf_path: str, expected_total: int) -> tuple[list, dict]:
    """
    Extract order lines and PDF header fields from a purchase-order PDF.

    Returns:
        (order_lines, header_fields)

        order_lines: list of dicts with keys:
            product_code, quantity, unit_price, line_total
            optional: product_name
        header_fields: dict with keys:
            pdf_so_number, pdf_order_date, pdf_customer_name, pdf_customer_code

    Raises ValueError if extraction fails hard (caller decides whether to skip or fail).
    """
    if not pdf_path or not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    with pdfplumber.open(pdf_path) as pdf:
        header_fields = _extract_header_fields_from_pdf(pdf)
        order_lines = _extract_lines_from_tables(pdf, expected_total)

    return order_lines, header_fields


def _extract_lines_from_tables(pdf, expected_total: int) -> list:
    """Try table extraction first, then text-regex fallback."""
    lines = _table_extraction(pdf)
    if _total_matches(lines, expected_total):
        return lines

    lines_fallback = _regex_fallback(pdf)
    if _total_matches(lines_fallback, expected_total):
        return lines_fallback

    # Return whichever got more lines; let validator raise
    return lines if len(lines) >= len(lines_fallback) else lines_fallback


def _table_extraction(pdf) -> list:
    order_lines = []
    col_map = {}

    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            if not table or len(table) < 2:
                continue

            # Detect header row — try first two rows
            for header_idx in range(min(2, len(table))):
                detected = _detect_column_indices(table[header_idx])

                # Need at least: ma_hang, sl, don_gia, thanh_tien
                # ten_sp is optional, used only for product auto-create.
                if all(k in detected for k in ("ma_hang", "sl", "don_gia", "thanh_tien")):
                    col_map = detected
                    data_start = header_idx + 1
                    break
            else:
                continue  # no valid header found in this table

            for row in table[data_start:]:
                if not row or len(row) < max(col_map.values()) + 1:
                    continue

                cells = [
                    str(c).replace("\n", " ").strip() if c else ""
                    for c in row
                ]

                product_code = cells[col_map["ma_hang"]].strip()

                # Skip totals rows and empty rows
                if not product_code or re.search(r"tổng|total|cộng", product_code, re.IGNORECASE):
                    continue

                product_name = None
                if "ten_sp" in col_map:
                    product_name = cells[col_map["ten_sp"]].strip() or None

                try:
                    line_item = {
                        "product_code": product_code,
                        "quantity": _parse_int(cells[col_map["sl"]]),
                        "unit_price": _parse_int(cells[col_map["don_gia"]]),
                        "line_total": _parse_int(cells[col_map["thanh_tien"]]),
                    }

                    if product_name:
                        line_item["product_name"] = product_name

                    order_lines.append(line_item)

                except (ValueError, IndexError):
                    continue  # skip malformed rows, don't abort

    return order_lines


def _regex_fallback(pdf) -> list:
    """
    Fallback: scan raw text lines for rows matching the product line pattern.
    Pattern: product_code (alphanumeric, 10-20 chars) ... quantity ... unit_price ... line_total
    """
    fallback_lines = []
    for page in pdf.pages:
        text = page.extract_text() or ""
        for line in text.split("\n"):
            # Match: CODE  (optional description)  QTY  PRICE  TOTAL
            m = re.search(
                r"([A-Z0-9][A-Z0-9._-]{9,19})"   # product_code: 10-20 chars
                r".*?"
                r"\b(\d{1,5})\s+"                  # quantity: 1-5 digits
                r"([\d.,]{5,})\s+"                 # unit_price: at least 5 chars (e.g. 1.898.148)
                r"([\d.,]{5,})",                   # line_total
                line,
            )
            if m:
                try:
                    fallback_lines.append({
                        "product_code": m.group(1),
                        "quantity": _parse_int(m.group(2)),
                        "unit_price": _parse_int(m.group(3)),
                        "line_total": _parse_int(m.group(4)),
                    })
                except ValueError:
                    pass
    return fallback_lines


def _total_matches(lines: list, expected: int) -> bool:
    if not lines:
        return False
    if expected == 0:
        return True  # can't verify; treat as pass
    return sum(item["line_total"] for item in lines) == expected