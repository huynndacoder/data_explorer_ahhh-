from loaders import _conn
import re
import unicodedata

MANUAL_PRODUCT_NAME_MAP = {
    "1010130010100000": "Xe đạp Thống Nhất REX Xanh ngọc",
    "000219002001000": "Xe đạp Thống Nhất GN 2.0 700C đen",
    "000218003022001": "Xe đạp Thống Nhất GN 06-27 2.0 Pro Shimano Xanh",
    "1000400050040003": "Xe đạp Thống Nhất MTB SPD 27.5 17 DA Kyolic",
    "000225002004003": "Xe đạp Thống Nhất New 26 DA Kyolic",
    "TP0099.0000570": "Xe đạp Thống Nhất Unite 26",
    "TP0099.0000571": "Xe đạp Thống Nhất Unite 27.5",
    "156.01.12.0003": "Xe đạp Thống Nhất unite 20",
    "TP0022.02.16.00": "Xe đạp Thống Nhất TE 16 02",
    "1010020000220000": "Xe đạp Thống Nhất GRX AT 27,5_2.0_15 Xanh dương",
    "000306002022000": "Xe đạp Thống Nhất MTB 20-05 S xanh",
    "TP0099.0000567": "Xe đạp Thống Nhất SLX 26 01",
    "TP0023.02.25.00": "Xe đạp Thống Nhất nam",
    "TP0017.06.27.04": "Xe đạp Thống Nhất The flash 27 01",
    "TP0099.0000568": "Xe đạp Thống Nhất SLX 27,5 - 01",
    "TP0022.03.16.00": "Xe đạp Thống Nhất TE 16 03",
    "000216002022009": "Xe đạp Thống Nhất GN 06 24 D xanh DA Bno Vint",
    "TP0016.05.24.01": "Xe đạp Thống Nhất GN 05 24",
}



def apply_manual_product_names() -> int:
    """
    Replace UNRESOLVED PRODUCT names with manually verified product names.

    Only updates rows where:
    - product_code exists in MANUAL_PRODUCT_NAME_MAP
    - current product_name is exactly 'UNRESOLVED PRODUCT {product_code}'

    This prevents overwriting existing good product names.
    Safe to run multiple times.
    """
    if not MANUAL_PRODUCT_NAME_MAP:
        print("[SILVER_PRODUCT_NAMES] no manual product mappings configured")
        return 0

    updated_count = 0

    with _conn() as conn, conn.cursor() as cur:
        for product_code, verified_name in MANUAL_PRODUCT_NAME_MAP.items():
            product_code = str(product_code).strip()
            verified_name = str(verified_name).strip()

            if not product_code or not verified_name:
                continue

            unresolved_name = f"UNRESOLVED PRODUCT {product_code}"

            cur.execute(
                """
                UPDATE tnbike.product
                SET product_name = %s
                WHERE product_code = %s
                  AND product_name = %s
                """,
                (
                    verified_name,
                    product_code,
                    unresolved_name,
                ),
            )

            row_count = cur.rowcount
            updated_count += row_count

            if row_count > 0:
                print(
                    f"[SILVER_PRODUCT_NAME_UPDATE] "
                    f"product_code={product_code} "
                    f"old_name={unresolved_name} "
                    f"new_name={verified_name}"
                )

        conn.commit()

    print(f"[SILVER_PRODUCT_NAMES] updated_count={updated_count}")
    return updated_count

def unresolved_product_summary() -> dict:
    """
    Return summary of unresolved product rows after manual product-name fixes.
    """
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                COUNT(DISTINCT p.product_code) AS unresolved_product_count,
                COUNT(ol.line_id) AS affected_order_lines,
                COALESCE(SUM(ol.quantity), 0) AS affected_quantity,
                COALESCE(SUM(ol.line_total), 0) AS affected_revenue
            FROM tnbike.product p
            LEFT JOIN tnbike.order_line ol
                ON p.product_code = ol.product_code
            WHERE p.product_name LIKE 'UNRESOLVED PRODUCT %'
            """
        )

        row = cur.fetchone()

    summary = {
        "unresolved_product_count": row[0],
        "affected_order_lines": int(row[1] or 0),
        "affected_quantity": float(row[2] or 0),
        "affected_revenue": float(row[3] or 0),
    }

    print(f"[SILVER_UNRESOLVED_PRODUCT_SUMMARY] {summary}")
    return summary

def normalize_customer_names() -> int:
    """
    Remove accidental leading field labels from tnbike.customer.customer_name.

    Examples:
        'Tên : CÔNG TY TNHH PHÚC AN'
        -> 'CÔNG TY TNHH PHÚC AN'

        'Khách hàng : CÔNG TY A'
        -> 'CÔNG TY A'

    Safe to run multiple times.
    """
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE tnbike.customer
            SET customer_name = regexp_replace(
                    customer_name,
                    '^(Tên|Ten|Đại\\s*lý|Dai\\s*ly|Khách\\s*hàng|Khach\\s*hang|Customer)\\s*[:\\-]\\s*',
                    '',
                    'i'
                ),
                updated_at = NOW()
            WHERE customer_name ~* '^(Tên|Ten|Đại\\s*lý|Dai\\s*ly|Khách\\s*hàng|Khach\\s*hang|Customer)\\s*[:\\-]\\s*'
            """
        )

        updated_count = cur.rowcount
        conn.commit()

    print(f"[SILVER_CUSTOMER_NAME_NORMALIZE] updated_count={updated_count}")
    return updated_count

SILVER_PROVINCE_SOURCE = "Canonical Silver geography list for DataExplorer 2026"


SILVER_PROVINCES = [
    # province_code, province_name, province_type, region
    # Official post-merger 34 provincial-level units, effective from 2025-07-01.

    # Miền Bắc
    ("01", "Hà Nội", "Thành phố", "Miền Bắc"),
    ("04", "Cao Bằng", "Tỉnh", "Miền Bắc"),
    ("08", "Tuyên Quang", "Tỉnh", "Miền Bắc"),
    ("11", "Điện Biên", "Tỉnh", "Miền Bắc"),
    ("12", "Lai Châu", "Tỉnh", "Miền Bắc"),
    ("14", "Sơn La", "Tỉnh", "Miền Bắc"),
    ("15", "Lào Cai", "Tỉnh", "Miền Bắc"),
    ("19", "Thái Nguyên", "Tỉnh", "Miền Bắc"),
    ("20", "Lạng Sơn", "Tỉnh", "Miền Bắc"),
    ("22", "Quảng Ninh", "Tỉnh", "Miền Bắc"),
    ("24", "Bắc Ninh", "Tỉnh", "Miền Bắc"),
    ("25", "Phú Thọ", "Tỉnh", "Miền Bắc"),
    ("31", "Hải Phòng", "Thành phố", "Miền Bắc"),
    ("33", "Hưng Yên", "Tỉnh", "Miền Bắc"),
    ("37", "Ninh Bình", "Tỉnh", "Miền Bắc"),

    # Miền Trung
    ("38", "Thanh Hóa", "Tỉnh", "Miền Trung"),
    ("40", "Nghệ An", "Tỉnh", "Miền Trung"),
    ("42", "Hà Tĩnh", "Tỉnh", "Miền Trung"),
    ("44", "Quảng Trị", "Tỉnh", "Miền Trung"),
    ("46", "Huế", "Thành phố", "Miền Trung"),
    ("48", "Đà Nẵng", "Thành phố", "Miền Trung"),
    ("51", "Quảng Ngãi", "Tỉnh", "Miền Trung"),
    ("52", "Gia Lai", "Tỉnh", "Miền Trung"),
    ("56", "Khánh Hòa", "Tỉnh", "Miền Trung"),
    ("66", "Đắk Lắk", "Tỉnh", "Miền Trung"),
    ("68", "Lâm Đồng", "Tỉnh", "Miền Trung"),

    # Miền Nam
    ("75", "Đồng Nai", "Tỉnh", "Miền Nam"),
    ("79", "Thành phố Hồ Chí Minh", "Thành phố", "Miền Nam"),
    ("80", "Tây Ninh", "Tỉnh", "Miền Nam"),
    ("82", "Vĩnh Long", "Tỉnh", "Miền Nam"),
    ("86", "Cần Thơ", "Thành phố", "Miền Nam"),
    ("89", "Đồng Tháp", "Tỉnh", "Miền Nam"),
    ("91", "An Giang", "Tỉnh", "Miền Nam"),
    ("96", "Cà Mau", "Tỉnh", "Miền Nam"),
]

PROVINCE_ALIASES = {
    # =========================
    # MIỀN BẮC
    # =========================

    # 01 - Hà Nội, unchanged
    "ha noi": "01",
    "tp ha noi": "01",
    "thanh pho ha noi": "01",
    "ha no": "01",  # dirty spelling from source data

    # 04 - Cao Bằng, unchanged
    "cao bang": "04",

    # 08 - Tuyên Quang, merged from old Tuyên Quang + Hà Giang
    "tuyen quang": "08",
    "ha giang": "08",  # merged into Tuyên Quang

    # 11 - Điện Biên, unchanged
    "dien bien": "11",

    # 12 - Lai Châu, unchanged
    "lai chau": "12",

    # 14 - Sơn La, unchanged
    "son la": "14",

    # 15 - Lào Cai, merged from old Lào Cai + Yên Bái
    "lao cai": "15",
    "yen bai": "15",  # merged into Lào Cai

    # 19 - Thái Nguyên, merged from old Thái Nguyên + Bắc Kạn
    "thai nguyen": "19",
    "bac kan": "19",  # merged into Thái Nguyên

    # 20 - Lạng Sơn, unchanged
    "lang son": "20",

    # 22 - Quảng Ninh, unchanged
    "quang ninh": "22",
    "quang ninhso": "22",  # dirty spelling from source data

    # 24 - Bắc Ninh, merged from old Bắc Ninh + Bắc Giang
    "bac ninh": "24",
    "bac giang": "24",  # merged into Bắc Ninh

    # 25 - Phú Thọ, merged from old Phú Thọ + Vĩnh Phúc + Hòa Bình
    "phu tho": "25",
    "vinh phuc": "25",  # merged into Phú Thọ
    "hoa binh": "25",   # merged into Phú Thọ

    # 31 - Hải Phòng, merged from old Hải Phòng + Hải Dương
    "hai phong": "31",
    "tp hai phong": "31",
    "thanh pho hai phong": "31",
    "hai duong": "31",  # merged into Hải Phòng
    "hai duon": "31",   # dirty spelling from source data

    # 33 - Hưng Yên, merged from old Hưng Yên + Thái Bình
    "hung yen": "33",
    "thai binh": "33",  # merged into Hưng Yên

    # 37 - Ninh Bình, merged from old Ninh Bình + Hà Nam + Nam Định
    "ninh binh": "37",
    "ha nam": "37",    # merged into Ninh Bình
    "nam dinh": "37",  # merged into Ninh Bình


    # =========================
    # MIỀN TRUNG
    # =========================

    # 38 - Thanh Hóa, unchanged
    "thanh hoa": "38",

    # 40 - Nghệ An, unchanged
    "nghe an": "40",
    "nghe a": "40",  # dirty spelling from source data

    # 42 - Hà Tĩnh, unchanged
    "ha tinh": "42",

    # 44 - Quảng Trị, merged from old Quảng Trị + Quảng Bình
    "quang tri": "44",
    "quang binh": "44",  # merged into Quảng Trị

    # 46 - Huế, renamed/normalized from Thừa Thiên Huế / TP Huế
    "hue": "46",
    "tp hue": "46",
    "thanh pho hue": "46",
    "thua thien hue": "46",

    # 48 - Đà Nẵng, merged from old Đà Nẵng + Quảng Nam
    "da nang": "48",
    "tp da nang": "48",
    "thanh pho da nang": "48",
    "quang nam": "48",  # merged into Đà Nẵng
    "hoang sa": "48",  # special district under Đà Nẵng, not Khánh Hòa

    # 51 - Quảng Ngãi, merged from old Quảng Ngãi + Kon Tum
    "quang ngai": "51",
    "kon tum": "51",  # merged into Quảng Ngãi

    # 52 - Gia Lai, merged from old Gia Lai + Bình Định
    "gia lai": "52",
    "binh dinh": "52",  # merged into Gia Lai

    # 56 - Khánh Hòa, merged from old Khánh Hòa + Ninh Thuận
    "khanh hoa": "56",
    "ninh thuan": "56",  # merged into Khánh Hòa
    "truong sa": "56",   # special district under Khánh Hòa

    # 66 - Đắk Lắk, merged from old Đắk Lắk + Phú Yên
    "dak lak": "66",
    "dac lac": "66",
    "đak lak": "66",
    "đac lac": "66",
    "phu yen": "66",  # merged into Đắk Lắk

    # 68 - Lâm Đồng, merged from old Lâm Đồng + Bình Thuận + Đắk Nông
    "lam dong": "68",
    "binh thuan": "68",  # merged into Lâm Đồng
    "phan thiet": "68",  # old city in Bình Thuận, now maps to Lâm Đồng
    "dak nong": "68",    # merged into Lâm Đồng
    "dac nong": "68",    # spelling variant


    # =========================
    # MIỀN NAM
    # =========================

    # 75 - Đồng Nai, merged from old Đồng Nai + Bình Phước
    "dong nai": "75",
    "binh phuoc": "75",  # merged into Đồng Nai

    # 79 - Thành phố Hồ Chí Minh, merged from old HCMC + Bình Dương + Bà Rịa - Vũng Tàu
    "ho chi minh": "79",
    "tp ho chi minh": "79",
    "thanh pho ho chi minh": "79",
    "tphcm": "79",
    "sai gon": "79",
    "binh duong": "79",       # merged into HCMC
    "thu dau mot": "79",     # old city in Bình Dương, now maps to HCMC
    "ba ria vung tau": "79", # merged into HCMC
    "vung tau": "79",        # old city in Bà Rịa - Vũng Tàu, now maps to HCMC

    # 80 - Tây Ninh, merged from old Tây Ninh + Long An
    "tay ninh": "80",
    "long an": "80",  # merged into Tây Ninh

    # 82 - Vĩnh Long, merged from old Vĩnh Long + Bến Tre + Trà Vinh
    "vinh long": "82",
    "ben tre": "82",  # merged into Vĩnh Long
    "tra vinh": "82", # merged into Vĩnh Long

    # 86 - Cần Thơ, merged from old Cần Thơ + Hậu Giang + Sóc Trăng
    "can tho": "86",
    "tp can tho": "86",
    "thanh pho can tho": "86",
    "hau giang": "86", # merged into Cần Thơ
    "soc trang": "86", # merged into Cần Thơ

    # 89 - Đồng Tháp, merged from old Đồng Tháp + Tiền Giang
    "dong thap": "89",
    "tien giang": "89",  # merged into Đồng Tháp

    # 91 - An Giang, merged from old An Giang + Kiên Giang
    "an giang": "91",
    "kien giang": "91", # merged into An Giang
    "phu quoc": "91",   # old city in Kiên Giang, now maps to An Giang

    # 96 - Cà Mau, merged from old Cà Mau + Bạc Liêu
    "ca mau": "96",
    "bac lieu": "96",  # merged into Cà Mau
}

def _strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.replace("đ", "d").replace("Đ", "D")
    return text


def _normalize_geo_text(text: str | None) -> str:
    if not text:
        return ""

    text = _strip_accents(text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _infer_province_from_text(text: str | None) -> tuple[str | None, str | None]:
    """
    Return:
        (province_code, matched_alias)

    If no confident match:
        (None, None)
    """
    normalized = _normalize_geo_text(text)

    if not normalized:
        return None, None

    aliases = sorted(PROVINCE_ALIASES.keys(), key=len, reverse=True)

    for alias in aliases:
        if re.search(rf"\b{re.escape(alias)}\b", normalized):
            return PROVINCE_ALIASES[alias], alias

    return None, None

def seed_silver_provinces() -> int:
    """
    Upsert canonical Silver province rows.
    Safe to run multiple times.
    """
    upsert_count = 0

    with _conn() as conn, conn.cursor() as cur:
        for code, name, province_type, region in SILVER_PROVINCES:
            cur.execute(
                """
                INSERT INTO tnbike.silver_province (
                    province_code,
                    province_name,
                    province_type,
                    region,
                    source,
                    is_active
                )
                VALUES (%s, %s, %s, %s, %s, TRUE)
                ON CONFLICT (province_code)
                DO UPDATE SET
                    province_name = EXCLUDED.province_name,
                    province_type = EXCLUDED.province_type,
                    region = EXCLUDED.region,
                    source = EXCLUDED.source,
                    is_active = TRUE
                """,
                (
                    code,
                    name,
                    province_type,
                    region,
                    SILVER_PROVINCE_SOURCE,
                ),
            )

            upsert_count += cur.rowcount

        conn.commit()

    print(f"[SILVER_PROVINCE_SEED] upsert_count={upsert_count}")
    return upsert_count

def build_silver_customer_geo() -> int:
    """
    Build customer_code -> canonical province_code mapping.

    Matching priority:
    1. customer.address
    2. legacy province.province_name as fallback

    Does not modify tnbike.customer.province_id.
    Writes trusted mapping into tnbike.silver_customer_geo.
    """
    seed_silver_provinces()

    upsert_count = 0
    unmatched_count = 0

    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                c.customer_code,
                c.address,
                c.province_id AS legacy_province_id,
                p.province_name AS legacy_province_name
            FROM tnbike.customer c
            LEFT JOIN tnbike.province p
                ON c.province_id = p.province_id
            ORDER BY c.customer_code
            """
        )

        rows = cur.fetchall()

        for customer_code, address, legacy_province_id, legacy_province_name in rows:
            province_code, matched_alias = _infer_province_from_text(address)
            match_method = "address"

            if province_code is None and legacy_province_name:
                province_code, matched_alias = _infer_province_from_text(legacy_province_name)
                match_method = "legacy_province_name"

            if province_code is None:
                unmatched_count += 1
                print(
                    f"[SILVER_CUSTOMER_GEO_UNMATCHED] "
                    f"customer_code={customer_code} "
                    f"address={address} "
                    f"legacy_province_id={legacy_province_id} "
                    f"legacy_province_name={legacy_province_name}"
                )
                continue

            cur.execute(
                """
                INSERT INTO tnbike.silver_customer_geo (
                    customer_code,
                    province_code,
                    source_address,
                    legacy_province_id,
                    legacy_province_name,
                    matched_text,
                    match_method,
                    confidence,
                    updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'HIGH', NOW())
                ON CONFLICT (customer_code)
                DO UPDATE SET
                    province_code = EXCLUDED.province_code,
                    source_address = EXCLUDED.source_address,
                    legacy_province_id = EXCLUDED.legacy_province_id,
                    legacy_province_name = EXCLUDED.legacy_province_name,
                    matched_text = EXCLUDED.matched_text,
                    match_method = EXCLUDED.match_method,
                    confidence = EXCLUDED.confidence,
                    updated_at = NOW()
                """,
                (
                    customer_code,
                    province_code,
                    address,
                    legacy_province_id,
                    legacy_province_name,
                    matched_alias,
                    match_method,
                ),
            )

            upsert_count += cur.rowcount

        conn.commit()

    print(
        f"[SILVER_CUSTOMER_GEO] "
        f"upsert_count={upsert_count} unmatched_count={unmatched_count}"
    )
    return upsert_count


def silver_geo_summary() -> dict:
    """
    Summarize Silver geography coverage.
    """
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM tnbike.silver_province")
        silver_province_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM tnbike.customer")
        customer_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM tnbike.silver_customer_geo")
        mapped_customer_count = cur.fetchone()[0]

        cur.execute(
            """
            SELECT COUNT(*)
            FROM tnbike.customer c
            LEFT JOIN tnbike.silver_customer_geo scg
                ON c.customer_code = scg.customer_code
            WHERE scg.customer_code IS NULL
            """
        )
        unmatched_customer_count = cur.fetchone()[0]

    summary = {
        "silver_province_count": silver_province_count,
        "customer_count": customer_count,
        "mapped_customer_count": mapped_customer_count,
        "unmatched_customer_count": unmatched_customer_count,
    }

    print(f"[SILVER_GEO_SUMMARY] {summary}")
    return summary


def silver_quality_summary() -> dict: ...


def run_silver_layer() -> dict:
    result = {}

    result["normalized_customer_names"] = normalize_customer_names()
    result["manual_product_names_updated"] = apply_manual_product_names()
    result["unresolved_products"] = unresolved_product_summary()

    result["silver_customer_geo_built"] = build_silver_customer_geo()
    result["silver_geo_summary"] = silver_geo_summary()

    print(f"[SILVER_LAYER_RESULT] {result}")
    return result
