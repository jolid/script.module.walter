CREATE TABLE IF NOT EXISTS wt_version (version INTEGER PRIMARY KEY);

CREATE TABLE IF NOT EXISTS wt_download_queue ( "qid" INTEGER  PRIMARY KEY AUTOINCREMENT, "type" TEXT, "description" TEXT, "url" TEXT, "src" TEXT, "folder" TEXT, "status" INTEGER DEFAULT (0), "num" INTEGER, "ts" TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE IF NOT EXISTS "wt_player_state" (  "playid" INTEGER  PRIMARY KEY AUTOINCREMENT, "hash" TEXT, "current" TEXT, "total" TEXT, "percent" TEXT, "state" TEXT, UNIQUE (hash) ON CONFLICT REPLACE);

CREATE UNIQUE INDEX IF NOT EXISTS "unique_url" on wt_download_queue (url ASC);

CREATE UNIQUE INDEX IF NOT EXISTS "unique_hash" on wt_player_state (hash ASC);
