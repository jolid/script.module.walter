CREATE TABLE IF NOT EXISTS wt_version (version INTEGER PRIMARY KEY);

CREATE TABLE IF NOT EXISTS "wt_download_queue" ("queueid" INTEGER PRIMARY KEY AUTOINCREMENT, "filename" TEXT, "description" TEXT, "url" TEXT);

CREATE UNIQUE INDEX IF NOT EXISTS "unique_url" on wt_download_queue (url ASC);
