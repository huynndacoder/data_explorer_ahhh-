# loaders.py
import psycopg2
from datetime import datetime
from warehouse import DB_CONFIG
from airflow.utils.log.logging_mixin import LoggingMixin

log = LoggingMixin().log


def _conn():
    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        cur.execute("SET search_path TO tnbike, public;")
    return conn


def upsert_email_log(email_data: dict, status: str, error_msg: str | None = None):
    # Schema encodes error into processing_status: "Success" or "Failed: <reason>"
    if error_msg:
        processing_status = f"Failed: {error_msg[:200]}"  # cap length for safety
    else:
        processing_status = "Success"

    sql = """
        INSERT INTO tnbike.email_log
            (message_id, from_address, received_at, attachment_name, processing_status)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (message_id) DO UPDATE SET
            processing_status = EXCLUDED.processing_status
    """
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            sql,
            (
                email_data.get("message_id"),
                email_data.get("from_address"),
                email_data.get("received_at"),
                email_data.get("attachment_name"),
                processing_status,
            ),
        )


def upsert_sales_order(email_data: dict, header_fields: dict) -> int:
    """Insert or update sales_order. Returns order_id (PK)."""
    so_number = email_data.get("anchor_so_number") or header_fields.get("pdf_so_number")

    order_date_raw = header_fields.get("pdf_order_date")
    order_date = None
    if order_date_raw:
        try:
            order_date = datetime.strptime(order_date_raw, "%d/%m/%Y").date()
        except ValueError:
            pass

    customer_code_raw = email_data.get("anchor_customer_code") or header_fields.get(
        "pdf_customer_code"
    )
    # Look up actual customer_code from the customer table by MST
    customer_code = get_or_create_customer_code(
        customer_code_raw,
        customer_name=email_data.get("anchor_customer_name"),
        customer_address=email_data.get("anchor_customer_address"),
    )

    sql = """
        INSERT INTO tnbike.sales_order
            (so_number, order_date, customer_code, total_amount)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (so_number) DO UPDATE SET
            order_date    = EXCLUDED.order_date,
            customer_code = EXCLUDED.customer_code,
            total_amount  = EXCLUDED.total_amount
        RETURNING order_id
    """
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            sql,
            (
                so_number,
                order_date,
                customer_code,
                email_data.get("anchor_total_amount", 0),
            ),
        )
        return cur.fetchone()[0]


def upsert_order_lines(order_id: int, so_number: str, lines: list[dict]):
    """Delete existing lines for this order, then insert fresh (idempotent)."""
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM tnbike.order_line WHERE order_id = %s", (order_id,))
        cur.executemany(
            """
            INSERT INTO tnbike.order_line
                (order_id, so_number, product_code, quantity, unit_price, line_total)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            [
                (
                    order_id,
                    so_number,
                    ln["product_code"],
                    ln["quantity"],
                    ln["unit_price"],
                    ln["line_total"],
                )
                for ln in lines
            ],
        )

def get_or_create_customer_code(
        mst: str | None,
        customer_name: str | None = None,
        customer_address: str | None = None,
    ) -> str:
        """
        Resolve MST/tax_code from email/PDF to internal customer_code.

        If MST already exists in tnbike.customer.tax_code:
            return existing customer_code

        If MST is missing:
            raise ValueError, because we cannot identify the customer safely.

        If MST does not exist:
            create a minimal customer row:
                customer_code = next KH-xxxxx
                customer_name = extracted name or UNKNOWN CUSTOMER
                tax_code = MST
                address = extracted address
                province_id = NULL
                customer_tier/is_active/created_at/updated_at use DEFAULT

        Important:
            This function is safe for parallel Airflow mapped tasks because it locks
            tnbike.customer while generating the next KH-xxxxx code.
        """
        if not mst:
            raise ValueError(
                "missing_customer: no MST/tax_code found in email body; "
                f"name={customer_name}; address={customer_address}"
            )

        clean_mst = mst.strip()
        clean_name = (customer_name or "").strip() or "UNKNOWN CUSTOMER"
        clean_address = (customer_address or "").strip() or None

        with _conn() as conn, conn.cursor() as cur:
            # First check without lock for normal existing customers.
            cur.execute(
                """
                SELECT customer_code
                FROM tnbike.customer
                WHERE tax_code = %s
                LIMIT 1
                """,
                (clean_mst,),
            )
            row = cur.fetchone()

            if row:
                customer_code = row[0]
                print(
                    f"[CUSTOMER_RESOLVE] existing customer "
                    f"mst={clean_mst} customer_code={customer_code}"
                )
                return customer_code

            # Missing customer. Lock table before generating KH-xxxxx.
            # This prevents two parallel Airflow tasks from generating the same code.
            cur.execute("LOCK TABLE tnbike.customer IN SHARE ROW EXCLUSIVE MODE;")

            # Re-check after lock in case another parallel task inserted this MST.
            cur.execute(
                """
                SELECT customer_code
                FROM tnbike.customer
                WHERE tax_code = %s
                LIMIT 1
                """,
                (clean_mst,),
            )
            row = cur.fetchone()

            if row:
                customer_code = row[0]
                print(
                    f"[CUSTOMER_RESOLVE] existing customer after lock "
                    f"mst={clean_mst} customer_code={customer_code}"
                )
                return customer_code

            # Generate next KH-xxxxx safely while table is locked.
            cur.execute(
                """
                SELECT COALESCE(
                    MAX(CAST(SUBSTRING(customer_code FROM 4) AS INTEGER)),
                    0
                )
                FROM tnbike.customer
                WHERE customer_code ~ '^KH-[0-9]+$'
                """
            )
            max_num = cur.fetchone()[0]
            next_num = max_num + 1
            new_customer_code = f"KH-{next_num:05d}"

            cur.execute(
                """
                INSERT INTO tnbike.customer (
                    customer_code,
                    customer_name,
                    tax_code,
                    address,
                    province_id
                )
                VALUES (%s, %s, %s, %s, NULL)
                """,
                (
                    new_customer_code,
                    clean_name,
                    clean_mst,
                    clean_address,
                ),
            )

            conn.commit()

            print(
                f"[CUSTOMER_CREATE] new customer "
                f"customer_code={new_customer_code} "
                f"mst={clean_mst} "
                f"name={clean_name} "
                f"address={clean_address} "
                f"province_id=NULL"
            )

            return new_customer_code