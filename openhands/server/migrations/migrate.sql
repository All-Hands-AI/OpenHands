-- Check if table exists, if not create it
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    conversation_id VARCHAR NOT NULL,
    published BOOLEAN NOT NULL
);

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
END
$$;
