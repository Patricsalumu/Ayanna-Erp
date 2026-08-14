ALTER TABLE compta_classes ADD COLUMN IF NOT EXISTS date_creation DATETIME NULL;
ALTER TABLE compta_classes ADD COLUMN IF NOT EXISTS date_modification DATETIME NULL;
UPDATE compta_classes SET date_creation = created_at WHERE date_creation IS NULL AND created_at IS NOT NULL;
UPDATE compta_classes SET date_modification = updated_at WHERE date_modification IS NULL AND updated_at IS NOT NULL;
