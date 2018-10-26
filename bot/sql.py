CREATE_TABLE_TORRENTS = """CREATE TABLE IF NOT EXISTS Torrents (
    id NVARCHAR PRIMARY KEY,
    title NVARCHAR,
    description NVARCHAR DEFAULT NULL,
    magnet NVARCHAR,
    update_datetime TIMESTAMP DEFAULT NULL
);"""

CREATE_TABLE_GENERAL = """CREATE TABLE IF NOT EXISTS General (
    key NVARCHAR PRIMARY KEY,
    value NVARCHAR
);"""

CREATE_TABLE_PARSING_ERRORS = """CREATE TABLE IF NOT EXISTS ParsingErrors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    html NVARCHAR,
    error_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""

INSERT_DEFAULT_GENERAL_DATA = """INSERT OR IGNORE INTO General (key, value)
VALUES (?, ?);"""

INSERT_TORRENT = """INSERT OR REPLACE INTO Torrents (id, title, description, magnet, update_datetime)
VALUES (?, ?, ?, ?, ?);"""

INSERT_PARSING_ERROR = """INSERT INTO ParsingErrors (html)
VALUES (?);"""

SELECT_GENERAL_SETTING = """SELECT value
FROM General
WHERE key = ?;"""

UPDATE_GENERAL_SETTING = """UPDATE General
SET value = ?
WHERE key = ?;"""

SELECT_TORRENTS_COUNT = """SELECT COUNT(*)
FROM Torrents;"""

SELECT_TORRENT = """SELECT *
FROM Torrents
WHERE {} LIKE ?;"""

UPDATE_QUERIES_COUNT = """UPDATE General
SET value = value + {}
WHERE key = 'searches_count';"""
