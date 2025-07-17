-- Check if table exists, if not create it
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    conversation_id VARCHAR NOT NULL,
    published BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS research_views (
    id SERIAL PRIMARY KEY,
    conversation_id VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR,
    user_agent VARCHAR
);

Create Table IF NOT EXISTS research_trendings (
    id SERIAL PRIMARY KEY,
    conversation_id VARCHAR NOT NULL,
    total_view_24h INT NOT NULL DEFAULT 0,
    total_view_7d INT NOT NULL DEFAULT 0,
    total_view_30d INT NOT NULL DEFAULT 0
);

Create Table IF NOT EXISTS mem0_conversation_jobs (
    id SERIAL PRIMARY KEY,
    conversation_id VARCHAR NOT NULL,
    events JSONB NOT NULL,
    metadata JSONB NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'pending',
    error VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversation_events (
    id SERIAL PRIMARY KEY,
    conversation_id VARCHAR NOT NULL,
    event_id INT,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create compound index for conversation_events (conversation_id, event_id)
CREATE INDEX IF NOT EXISTS idx_conversation_events_conversation_event
ON conversation_events(conversation_id, event_id);

CREATE TABLE IF NOT EXISTS user_settings (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    settings JSONB
);

-- Create index for user_settings.user_id if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);

CREATE TABLE IF NOT EXISTS agent_states (
    id SERIAL PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_states_conversation_id ON agent_states(conversation_id);

-- Check if configs column exists, if not add it
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM information_schema.columns
        WHERE table_name = 'conversations'
        AND column_name = 'configs'
    ) THEN
        ALTER TABLE conversations
        ADD COLUMN configs JSONB NOT NULL DEFAULT '{}';
    END IF;

    -- Add title column if it doesn't exist
    IF NOT EXISTS (
        SELECT FROM information_schema.columns
        WHERE table_name = 'conversations'
        AND column_name = 'title'
    ) THEN
        ALTER TABLE conversations
        ADD COLUMN title VARCHAR(255);
    END IF;

    -- Add short_description column if it doesn't exist
    IF NOT EXISTS (
        SELECT FROM information_schema.columns
        WHERE table_name = 'conversations'
        AND column_name = 'short_description'
    ) THEN
        ALTER TABLE conversations
        ADD COLUMN short_description TEXT;
    END IF;

    -- add created_at column if it doesn't exist
    IF NOT EXISTS (
        SELECT FROM information_schema.columns
        WHERE table_name = 'conversations'
        AND column_name = 'created_at'
    ) THEN
        ALTER TABLE conversations
        ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
    END IF;

    IF NOT EXISTS (
        SELECT FROM information_schema.columns
        WHERE table_name = 'conversations'
        AND column_name = 'status'
    ) THEN
        ALTER TABLE conversations
        ADD COLUMN status VARCHAR DEFAULT 'available';
    END IF;

     IF NOT EXISTS (
        SELECT FROM information_schema.columns
        WHERE table_name = 'conversations'
        AND column_name = 'metadata'
    ) THEN
        ALTER TABLE conversations
        ADD COLUMN metadata JSONB NOT NULL DEFAULT '{}';
    END IF;
END;
$$;
