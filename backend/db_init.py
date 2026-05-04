import sqlite3
from pathlib import Path

DB_PATH = Path.home() / 'Desktop' / 'mission-control' / 'backend' / 'mission_control.db'

def init_db():
    """Create tables if they don't exist."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute('PRAGMA journal_mode=WAL')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL UNIQUE,
            project     TEXT,
            started_at  INTEGER NOT NULL,
            ended_at    INTEGER,
            status      TEXT DEFAULT 'active'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tool_events (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      TEXT NOT NULL,
            event_type      TEXT NOT NULL,
            tool_name       TEXT NOT NULL,
            tool_input_json TEXT,
            exit_code       INTEGER,
            duration_ms     INTEGER,
            created_at      INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tool_events_session ON tool_events(session_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tool_events_created ON tool_events(created_at DESC)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL,
            file_path   TEXT NOT NULL,
            event_type  TEXT NOT NULL,
            created_at  INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_events_created ON file_events(created_at DESC)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS token_usage (
            id                          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id                  TEXT NOT NULL,
            message_id                  TEXT,
            model                       TEXT,
            input_tokens                INTEGER DEFAULT 0,
            output_tokens               INTEGER DEFAULT 0,
            cache_read_tokens           INTEGER DEFAULT 0,
            cache_creation_tokens       INTEGER DEFAULT 0,
            created_at                  INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_token_usage_session ON token_usage(session_id)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT,
            title       TEXT NOT NULL,
            status      TEXT NOT NULL DEFAULT 'queued',
            project     TEXT,
            created_at  INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000),
            updated_at  INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cron_jobs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL UNIQUE,
            schedule        TEXT,
            command         TEXT,
            last_run_at     INTEGER,
            last_run_status TEXT,
            last_run_output TEXT,
            project         TEXT,
            created_at      INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS research_findings (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name        TEXT NOT NULL,
            finding_text      TEXT NOT NULL,
            source_url        TEXT,
            source_name       TEXT,
            importance_score  INTEGER,
            category          TEXT,
            status            TEXT DEFAULT 'pending_examination',
            created_at        INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000),
            updated_at        INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_research_findings_status ON research_findings(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_research_findings_agent ON research_findings(agent_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_research_findings_created ON research_findings(created_at DESC)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS examinations (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            finding_id        INTEGER NOT NULL,
            claude_analysis   TEXT NOT NULL,
            gameplan          TEXT NOT NULL,
            priority          TEXT,
            requires_approval INTEGER DEFAULT 0,
            status            TEXT DEFAULT 'pending_action',
            trade_action      TEXT,
            created_at        INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000),
            updated_at        INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000),

            FOREIGN KEY (finding_id) REFERENCES research_findings(id)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_examinations_status ON examinations(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_examinations_finding ON examinations(finding_id)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS actions (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            examination_id    INTEGER NOT NULL,
            action_type       TEXT NOT NULL,
            action_description TEXT,
            result            TEXT,
            result_detail     TEXT,
            created_at        INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000),
            executed_at       INTEGER,

            FOREIGN KEY (examination_id) REFERENCES examinations(id)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_actions_status ON actions(action_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_actions_examination ON actions(examination_id)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS examination_conversations (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            examination_id    INTEGER NOT NULL,
            role              TEXT NOT NULL,
            message           TEXT NOT NULL,
            created_at        INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000),

            FOREIGN KEY (examination_id) REFERENCES examinations(id)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_examination_conversations ON examination_conversations(examination_id)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cost_alerts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            threshold_pct   INTEGER NOT NULL,
            budget          REAL NOT NULL,
            cost_at_trigger REAL NOT NULL,
            alert_date      TEXT NOT NULL,
            sent_via        TEXT,
            created_at      INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cost_alerts_date ON cost_alerts(alert_date)')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_examinations_trade_action ON examinations(trade_action) WHERE trade_action IS NOT NULL')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_token_usage_model ON token_usage(model)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_token_usage_created ON token_usage(created_at DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_paper_trades_ticker ON paper_trades(ticker)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_paper_trades_created ON paper_trades(created_at DESC)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS paper_portfolio (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker      TEXT NOT NULL UNIQUE,
            shares      REAL NOT NULL DEFAULT 0,
            avg_cost    REAL NOT NULL DEFAULT 0,
            updated_at  INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS paper_trades (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker          TEXT NOT NULL,
            action          TEXT NOT NULL,
            shares          REAL NOT NULL,
            price           REAL NOT NULL,
            cash_impact     REAL NOT NULL,
            reason          TEXT,
            finding_id      INTEGER,
            created_at      INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS paper_cash (
            id          INTEGER PRIMARY KEY,
            balance     REAL NOT NULL DEFAULT 5000.0,
            updated_at  INTEGER NOT NULL DEFAULT (strftime('%s','now') * 1000)
        )
    ''')
    cursor.execute('INSERT OR IGNORE INTO paper_cash (id, balance) VALUES (1, 5000.0)')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print(f"Database initialized at {DB_PATH}")
