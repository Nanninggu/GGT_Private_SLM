-- Migration: Convert cmetadata column from json to jsonb
-- This enables proper JSONB operations and fixes type conversion errors

-- Step 1: Add a new jsonb column
ALTER TABLE langchain_pg_collection 
ADD COLUMN IF NOT EXISTS cmetadata_new JSONB;

-- Step 2: Copy data from json to jsonb column
UPDATE langchain_pg_collection 
SET cmetadata_new = cmetadata::jsonb
WHERE cmetadata IS NOT NULL;

-- Step 3: Drop the old json column
ALTER TABLE langchain_pg_collection 
DROP COLUMN IF EXISTS cmetadata;

-- Step 4: Rename the new column to the original name
ALTER TABLE langchain_pg_collection 
RENAME COLUMN cmetadata_new TO cmetadata;

-- Step 5: Add comment
COMMENT ON COLUMN langchain_pg_collection.cmetadata IS 'Collection metadata in JSONB format for better performance and operations';
