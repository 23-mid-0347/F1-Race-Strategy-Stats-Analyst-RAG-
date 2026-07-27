CREATE TABLE IF NOT EXISTS drivers (
    driver_id       SERIAL PRIMARY KEY,
    driver_code     TEXT UNIQUE NOT NULL,
    full_name       TEXT NOT NULL,
    nationality     TEXT,
    date_of_birth   DATE
);

CREATE TABLE IF NOT EXISTS constructors (
    constructor_id  SERIAL PRIMARY KEY,
    name            TEXT UNIQUE NOT NULL,
    nationality     TEXT
);

CREATE TABLE IF NOT EXISTS circuits (
    circuit_id      SERIAL PRIMARY KEY,
    name            TEXT UNIQUE NOT NULL,
    location        TEXT,
    country         TEXT
);

CREATE TABLE IF NOT EXISTS seasons (
    season_id       SERIAL PRIMARY KEY,
    year            INT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    event_id        SERIAL PRIMARY KEY,
    season_id       INT NOT NULL REFERENCES seasons(season_id),
    round           INT NOT NULL,
    event_name      TEXT NOT NULL,
    circuit_id      INT REFERENCES circuits(circuit_id),
    event_date      DATE,
    UNIQUE (season_id, round)
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id      SERIAL PRIMARY KEY,
    event_id        INT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    session_type    TEXT NOT NULL,
    session_date    TIMESTAMP,
    UNIQUE (event_id, session_type)
);

CREATE TABLE IF NOT EXISTS results (
    result_id       SERIAL PRIMARY KEY,
    session_id      INT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    driver_id       INT NOT NULL REFERENCES drivers(driver_id),
    constructor_id  INT REFERENCES constructors(constructor_id),
    grid_position   INT,
    finish_position INT,
    points          NUMERIC,
    status          TEXT,
    UNIQUE (session_id, driver_id)
);

CREATE TABLE IF NOT EXISTS lap_times (
    lap_id          SERIAL PRIMARY KEY,
    session_id      INT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    driver_id       INT NOT NULL REFERENCES drivers(driver_id),
    lap_number      INT NOT NULL,
    lap_time_ms     INT,
    tire_compound   TEXT,
    UNIQUE (session_id, driver_id, lap_number)
);

CREATE TABLE IF NOT EXISTS pit_stops (
    pit_stop_id     SERIAL PRIMARY KEY,
    session_id      INT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    driver_id       INT NOT NULL REFERENCES drivers(driver_id),
    stop_number     INT NOT NULL,
    lap             INT,
    duration_ms     INT,
    UNIQUE (session_id, driver_id, stop_number)
);

CREATE TABLE IF NOT EXISTS stints (
    stint_id        SERIAL PRIMARY KEY,
    session_id      INT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    driver_id       INT NOT NULL REFERENCES drivers(driver_id),
    stint_number    INT NOT NULL,
    compound        TEXT,
    lap_start       INT,
    lap_end         INT,
    UNIQUE (session_id, driver_id, stint_number)
);

CREATE TABLE IF NOT EXISTS weather (
    weather_id      SERIAL PRIMARY KEY,
    session_id      INT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    recorded_at     TIMESTAMP,
    air_temp        NUMERIC,
    track_temp      NUMERIC,
    humidity        NUMERIC,
    rainfall        BOOLEAN,
    wind_speed      NUMERIC,
    UNIQUE (session_id, recorded_at)
);

CREATE TABLE IF NOT EXISTS documents (
    doc_id          SERIAL PRIMARY KEY,
    event_id        INT REFERENCES events(event_id),
    source_url      TEXT,
    title           TEXT,
    content_type    TEXT,
    scraped_at      TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS embeddings_metadata (
    embedding_id        SERIAL PRIMARY KEY,
    doc_id               INT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    chunk_index          INT NOT NULL,
    chunk_text_preview   TEXT,
    vector_db_id         TEXT,
    created_at           TIMESTAMP DEFAULT now(),
    UNIQUE (doc_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_events_season ON events(season_id);
CREATE INDEX IF NOT EXISTS idx_sessions_event ON sessions(event_id);
CREATE INDEX IF NOT EXISTS idx_results_session ON results(session_id);
CREATE INDEX IF NOT EXISTS idx_results_driver ON results(driver_id);
CREATE INDEX IF NOT EXISTS idx_laptimes_session_driver ON lap_times(session_id, driver_id);
CREATE INDEX IF NOT EXISTS idx_pitstops_session_driver ON pit_stops(session_id, driver_id);
CREATE INDEX IF NOT EXISTS idx_stints_session_driver ON stints(session_id, driver_id);
CREATE INDEX IF NOT EXISTS idx_weather_session ON weather(session_id);
CREATE INDEX IF NOT EXISTS idx_documents_event ON documents(event_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_doc ON embeddings_metadata(doc_id);