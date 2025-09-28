-- Migration: Update existing shared collections to new structure
-- This migration updates existing shared collections (user_id = NULL) to have proper ownership tracking

-- Step 1: Update existing shared collections to have a system user_id
-- We'll use 'system' as the user_id for existing shared collections
UPDATE langchain_pg_collection 
SET user_id = 'system'
WHERE user_id IS NULL;

-- Step 2: Update metadata to include is_shared flag for existing collections
UPDATE langchain_pg_collection 
SET cmetadata = jsonb_set(
    COALESCE(cmetadata, '{}'::jsonb), 
    '{is_shared}', 
    'true'::jsonb
)
WHERE user_id = 'system';

-- Step 3: Add comment explaining the migration
COMMENT ON COLUMN langchain_pg_collection.user_id IS 'User ID for collection ownership. system means legacy shared collection.';
