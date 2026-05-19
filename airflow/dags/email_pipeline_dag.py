# dags/email_pipeline_dag.py
from __future__ import annotations
import os, glob
from datetime import datetime

from airflow.decorators import dag, task
from airflow.operators.python import get_current_context
from airflow.utils.log.logging_mixin import LoggingMixin

log = LoggingMixin().log

EML_DIR = "/opt/airflow/maildata/incoming/"
TEMP_PDF_DIR = "/tmp/pdf_staging/"
PROCESSED_DIR = "/opt/airflow/maildata/processed/"
FAILED_DIR = "/opt/airflow/maildata/failed/"


@dag(
    dag_id="email_order_pipeline",
    start_date=datetime(2026, 3, 1),
    schedule_interval=None,  # triggered manually or via sensor
    catchup=False,
    tags=["d28", "sales"],
    max_active_tasks=8,  # parallelism cap
)
def email_pipeline():

    @task
    def list_eml_files() -> list[str]:
        return sorted(glob.glob(os.path.join(EML_DIR, "*.eml")))

    @task(retries=1)
    def process_single_email(eml_path: str) -> dict:
        """
        Full per-email pipeline: extract → validate → load.
        Returns a status dict — never raises, always logs to email_log.
        """
        from extract import parse_email_and_extract_pdf, process_pdf_order
        from validators import validate_line_totals, ensure_products_exist
        from loaders import upsert_email_log, upsert_sales_order, upsert_order_lines
        from router import route_email

        os.makedirs(TEMP_PDF_DIR, exist_ok=True)
        email_data = None
        pdf_path = None
        status = "success"
        error_msg = None

        try:
            email_data, pdf_path = parse_email_and_extract_pdf(eml_path, TEMP_PDF_DIR)
            order_lines, header_fields = process_pdf_order(
                pdf_path, email_data["anchor_total_amount"]
            )
            validate_line_totals(order_lines, email_data["anchor_total_amount"])
            ensure_products_exist(order_lines)
            order_id = upsert_sales_order(email_data, header_fields)
            so_number = email_data.get("anchor_so_number") or header_fields.get(
                "pdf_so_number"
            )
            upsert_order_lines(order_id, so_number, order_lines)

        except Exception as exc:
            status = "failed"
            error_msg = str(exc)

        finally:
            if email_data:
                upsert_email_log(email_data, status, error_msg)
            route_email(eml_path, status, TEMP_PDF_DIR, PROCESSED_DIR, FAILED_DIR)

        return {"path": eml_path, "status": status, "error": error_msg}

    @task
    def summarize_results(results: list[dict]) -> dict:
        total = len(results)
        success = sum(1 for r in results if r.get("status") == "success")
        failed = sum(1 for r in results if r.get("status") == "failed")

        failure_counts = {}

        for r in results:
            if r.get("status") != "failed":
                continue

            error = r.get("error") or "unknown"

            if "missing_customer" in error:
                category = "missing_customer"
            elif "missing_product" in error:
                category = "missing_product"
            elif "qty×price" in error or "line_total" in error:
                category = "line_total_mismatch"
            else:
                category = "unknown"

            failure_counts[category] = failure_counts.get(category, 0) + 1

        print("========== EMAIL PIPELINE SUMMARY ==========")
        print(f"Total emails: {total}")
        print(f"Success: {success}")
        print(f"Failed: {failed}")
        print("Failures by category:")

        for category, count in sorted(failure_counts.items()):
            print(f"  {category}: {count}")

        return {
            "total": total,
            "success": success,
            "failed": failed,
            "failure_counts": failure_counts,
        }
    
    @task
    def run_silver_layer(summary: dict) -> dict:
        from silver import (
            normalize_customer_names,
            apply_manual_product_names,
            unresolved_product_summary,
            build_silver_customer_geo,
            silver_geo_summary,
        )

        print("========== RUN SILVER LAYER ==========")
        print(f"Successful emails: {summary.get('success')}")
        print(f"Failed emails: {summary.get('failed')}")

        result = {}

        # These two intentionally clean legacy dimensions 
        # They can affect refreshed fact_sales customer_name/product_name.
        result["normalized_customer_names"] = normalize_customer_names()
        result["manual_product_names_updated"] = apply_manual_product_names()

        # Read-only summary after product-name cleanup.
        result["unresolved_products"] = unresolved_product_summary()

        # These only affect Silver geography tables.
        # They do NOT change legacy customer.province_id or legacy fact_sales directly.
        result["silver_customer_geo_built"] = build_silver_customer_geo()
        result["silver_geo_summary"] = silver_geo_summary()

        print(f"[SILVER_LAYER_RESULT] {result}")
        return result

    @task
    def refresh_gold_fact(summary: dict, silver_result: dict, fact_result: dict) -> dict:
        from warehouse import refresh_gold_fact_sales

        print("========== REFRESH GOLD FACT SALES ==========")
        print(f"Successful emails: {summary.get('success')}")
        print(f"Failed emails: {summary.get('failed')}")
        print(f"Silver result: {silver_result}")
        print(f"Legacy fact result: {fact_result}")

        refresh_gold_fact_sales()

        return {
            "status": "success",
            "input_summary": summary,
            "silver_result": silver_result,
            "fact_result": fact_result,
        }


    @task
    def refresh_fact(summary: dict, silver_result: dict) -> dict:
        from warehouse import refresh_fact_sales

        print("========== REFRESH FACT SALES ==========")
        print(f"Successful emails: {summary.get('success')}")
        print(f"Failed emails: {summary.get('failed')}")
        print(f"Silver result: {silver_result}")

        refresh_fact_sales()

        return {
            "status": "success",
            "input_summary": summary,
            "silver_result": silver_result,
        }

    eml_files = list_eml_files()
    results = process_single_email.expand(eml_path=eml_files)

    summary = summarize_results(results)
    silver_result = run_silver_layer(summary)
    fact_result = refresh_fact(summary, silver_result)
    gold_result = refresh_gold_fact(summary, silver_result, fact_result)


email_pipeline()
