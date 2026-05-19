-- ============================================================
-- 12. EMAIL LOG  (email_log)
-- ============================================================
CREATE TABLE email_log (
    id                  SERIAL          PRIMARY KEY,
    message_id          TEXT            UNIQUE,
    from_address        TEXT,
    received_at         TIMESTAMP,
    attachment_name     TEXT,
    processing_status   TEXT            NOT NULL,
    created_at          TIMESTAMPTZ     DEFAULT NOW()
);

COMMENT ON TABLE  email_log                IS 'Audit log of processed email orders — tracks idempotency via message_id';
COMMENT ON COLUMN email_log.message_id     IS 'RFC 2822 Message-ID — used as unique dedup key';
COMMENT ON COLUMN email_log.processing_status IS 'Success | Failed (reason)';

CREATE INDEX idx_email_log_status ON email_log(processing_status);