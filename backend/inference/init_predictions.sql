CREATE TABLE IF NOT EXISTS predictions (
    task_id TEXT PRIMARY KEY,
    summary TEXT NOT NULL,
    description TEXT NOT NULL,
    label TEXT,
    probability FLOAT,
    status TEXT NOT NULL,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
