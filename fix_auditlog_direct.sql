-- Script SQL direct pour corriger le problème session_id NULL
-- À exécuter directement dans PostgreSQL si les migrations Django ne passent pas

-- 1. Faire le champ session_id nullable dans la table comptes_auditlog
ALTER TABLE comptes_auditlog ALTER COLUMN session_id DROP NOT NULL;

-- 2. Mettre à jour les enregistrements existants avec session_id NULL
UPDATE comptes_auditlog SET session_id = '' WHERE session_id IS NULL;

-- 3. Vérification
SELECT COUNT(*) as total_records, 
       COUNT(session_id) as non_null_session_ids,
       COUNT(*) - COUNT(session_id) as null_session_ids
FROM comptes_auditlog;

-- 4. Afficher les derniers enregistrements pour vérifier
SELECT id, type_action, description, session_id, date_heure 
FROM comptes_auditlog 
ORDER BY date_heure DESC 
LIMIT 5;
