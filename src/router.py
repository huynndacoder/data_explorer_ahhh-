import os
import shutil
import logging

logger = logging.getLogger(__name__)


def route_email(
    eml_path: str,
    status: str,
    temp_pdf_dir: str,
    processed_dir: str,
    failed_dir: str,
) -> dict:
    target_dir = processed_dir if status == "success" else failed_dir
    basename = os.path.basename(eml_path)
    target_path = os.path.join(target_dir, basename)

    moved_to = None
    pdf_cleaned = False

    try:
        if not os.path.exists(eml_path):
            logger.warning("EML already moved or missing: %s", eml_path)
        else:
            os.makedirs(target_dir, exist_ok=True)
            if os.path.exists(target_path):
                logger.warning("Target already exists, overwriting: %s", target_path)
                os.remove(target_path)
            shutil.move(eml_path, target_path)
            moved_to = target_path
            logger.info("Routed %s → %s (status=%s)", basename, target_dir, status)
    except OSError as exc:
        logger.error("Failed to move %s: %s", eml_path, exc)

    pdf_cleaned = _cleanup_temp_pdf(eml_path, temp_pdf_dir)

    return {"moved_to": moved_to, "pdf_cleaned": pdf_cleaned}


def _cleanup_temp_pdf(eml_path: str, temp_pdf_dir: str) -> bool:
    stem = os.path.splitext(os.path.basename(eml_path))[0]
    cleaned = False
    for fname in os.listdir(temp_pdf_dir) if os.path.isdir(temp_pdf_dir) else []:
        if fname.lower().startswith(stem.lower()) and fname.lower().endswith(".pdf"):
            try:
                os.remove(os.path.join(temp_pdf_dir, fname))
                cleaned = True
                logger.info("Removed temp PDF: %s", fname)
            except OSError as exc:
                logger.error("Failed to remove temp PDF %s: %s", fname, exc)
    return cleaned
