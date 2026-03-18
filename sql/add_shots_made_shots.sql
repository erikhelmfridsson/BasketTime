-- Lägg till skott och träff (shots, made_shots) i match_players.
-- Kör denna mot befintlig BasketTime-databas (t.ex. i pgAdmin) om tabellen redan finns utan dessa kolumner.

ALTER TABLE match_players
  ADD COLUMN IF NOT EXISTS shots INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS made_shots INTEGER NOT NULL DEFAULT 0;
