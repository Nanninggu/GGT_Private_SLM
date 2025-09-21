-- Migration: Add user_id column to langchain_pg_collection table
-- This enables user-specific collection isolation

-- Add user_id column to langchain_pg_collection table
ALTER TABLE langchain_pg_collection 
ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- Create index for user_id for better query performance
CREATE INDEX IF NOT EXISTS idx_langchain_pg_collection_user_id 
ON langchain_pg_collection (user_id);

-- Update existing collections to have NULL user_id (shared collections)
UPDATE langchain_pg_collection 
SET user_id = NULL 
WHERE user_id IS NULL;

-- Add comment to the table
COMMENT ON COLUMN langchain_pg_collection.user_id IS 'User ID for collection isolation. NULL means shared collection.';
