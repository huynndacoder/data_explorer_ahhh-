def validate_line_totals(
    lines: list,
    expected_total: int,
    line_tolerance_vnd: int = 1000,
    order_tolerance_vnd: int = 5000,
):
    """
    Validate extracted order lines before writing to DB.

    Business rule:
    - Missing/invalid fields are hard failures.
    - qty * unit_price may differ from extracted line_total by a tiny amount
      because of rounding/PDF formatting.
    - Small VND differences are accepted.
    - The extracted PDF/email line_total remains the source of truth.
    """
    if not lines:
        raise ValueError("No order lines extracted from PDF")

    for i, line in enumerate(lines, start=1):
        for field in ("product_code", "quantity", "unit_price", "line_total"):
            if line.get(field) is None:
                raise ValueError(f"Line {i}: missing field '{field}'")

        quantity = line["quantity"]
        unit_price = line["unit_price"]
        line_total = line["line_total"]

        if quantity <= 0:
            raise ValueError(f"Line {i}: quantity must be > 0, got {quantity}")

        if unit_price <= 0:
            raise ValueError(f"Line {i}: unit_price must be > 0, got {unit_price}")

        expected_line_total = round(quantity * unit_price)
        diff = abs(expected_line_total - line_total)

        if diff > line_tolerance_vnd:
            raise ValueError(
                f"Line {i}: qty×price={expected_line_total} ≠ "
                f"line_total={line_total}, diff={diff}đ, "
                f"tolerance={line_tolerance_vnd}đ"
            )

    if expected_total > 0:
        computed = round(sum(ln["line_total"] for ln in lines))
        diff = abs(computed - expected_total)

        if diff > order_tolerance_vnd:
            raise ValueError(
                f"Order total mismatch: PDF computed {computed:,}, "
                f"email declared {expected_total:,}, "
                f"diff={diff:,}đ, tolerance={order_tolerance_vnd:,}đ"
            )
        

def ensure_products_exist(order_lines: list) -> None:
    """
    Ensure that all extracted product_code values exist in tnbike.product.
    If product is missing:
        insert minimal product row.

    If product already exists but product_name is still UNRESOLVED PRODUCT ...:
        update it when parser provides a real product_name.

    This keeps FK integrity and allows gradual improvement of product master data.
    """
    from loaders import _conn

    product_map = {}

    for line in order_lines:
        product_code = str(line.get("product_code") or "").strip()
        if not product_code:
            continue

        product_name = line.get("product_name")
        if product_name:
            product_name = str(product_name).strip()

        if not product_name:
            product_name = f"UNRESOLVED PRODUCT {product_code}"

        if product_code not in product_map:
            product_map[product_code] = product_name

    product_codes = sorted(product_map.keys())

    if not product_codes:
        raise ValueError("missing_product: no product_code found in order lines")

    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT product_code, product_name
            FROM tnbike.product
            WHERE product_code = ANY(%s)
            """,
            (product_codes,),
        )

        existing_rows = {
            row[0]: row[1]
            for row in cur.fetchall()
        }

        for product_code, parsed_product_name in product_map.items():
            existing_name = existing_rows.get(product_code)

            if existing_name is None:
                cur.execute(
                    """
                    INSERT INTO tnbike.product (
                        product_code,
                        product_name,
                        line_id,
                        color,
                        unit
                    )
                    VALUES (%s, %s, NULL, NULL, 'Chiếc')
                    ON CONFLICT (product_code) DO NOTHING
                    """,
                    (product_code, parsed_product_name),
                )

                print(
                    f"[PRODUCT_CREATE] product "
                    f"product_code={product_code} "
                    f"product_name={parsed_product_name} "
                    f"line_id=NULL color=NULL unit=Chiếc"
                )

            else:
                unresolved_name = f"UNRESOLVED PRODUCT {product_code}"

                if (
                    existing_name == unresolved_name
                    and parsed_product_name
                    and parsed_product_name != unresolved_name
                ):
                    cur.execute(
                        """
                        UPDATE tnbike.product
                        SET product_name = %s,
                            created_at = NOW()
                        WHERE product_code = %s
                          AND product_name = %s
                        """,
                        (
                            parsed_product_name,
                            product_code,
                            unresolved_name,
                        ),
                    )

                    print(
                        f"[PRODUCT_UPDATE] resolved product_name "
                        f"product_code={product_code} "
                        f"old_name={unresolved_name} "
                        f"new_name={parsed_product_name}"
                    )

        conn.commit()