-- Create table if not exists
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    conversation_id VARCHAR NOT NULL,
    published BOOLEAN NOT NULL,
);

-- Alter configs column if exists
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
END
$$;
