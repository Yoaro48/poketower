-- Tabla de perfiles
DROP TABLE IF EXISTS perfiles;
CREATE TABLE IF NOT EXISTS perfiles (
    username TEXT PRIMARY KEY, 
    password_hash TEXT NOT NULL, 
    racha_actual INTEGER DEFAULT 0 CHECK(racha_actual >= 0), 
    ultima_fecha_jugada TEXT, -- Usamos TEXT para fechas en formato ISO (YYYY-MM-DD)
    mejor_racha INTEGER DEFAULT 0 CHECK(mejor_racha >= 0),
    email TEXT UNIQUE NOT NULL
);

-- Tabla de tiempos
DROP TABLE IF EXISTS tiempos;
CREATE TABLE IF NOT EXISTS tiempos (
    username TEXT, 
    completado INTEGER DEFAULT 0 CHECK (completado IN (0, 1)), -- SQLite no tiene BOOLEAN real, usa 0/1
    tiempo REAL CHECK(tiempo >= 0), 
    fecha TEXT, -- Usamos TEXT para consistencia
    FOREIGN KEY(username) REFERENCES perfiles(username)
);

DROP TRIGGER IF EXISTS actualizar_racha;

CREATE TRIGGER actualizar_racha
AFTER INSERT ON tiempos 
WHEN NEW.completado = 1
BEGIN
    UPDATE perfiles
    SET 
        racha_actual = CASE 
            WHEN ultima_fecha_jugada = date('now', '-1 day') THEN racha_actual + 1
            WHEN ultima_fecha_jugada = date('now') THEN racha_actual
            ELSE 1 
        END,
        
        mejor_racha = CASE 
            WHEN (
                CASE 
                    WHEN ultima_fecha_jugada = date('now', '-1 day') THEN racha_actual + 1
                    WHEN ultima_fecha_jugada = date('now') THEN racha_actual
                    ELSE 1 
                END
            ) > mejor_racha 
            THEN (
                CASE 
                    WHEN ultima_fecha_jugada = date('now', '-1 day') THEN racha_actual + 1
                    WHEN ultima_fecha_jugada = date('now') THEN racha_actual
                    ELSE 1 
                END
            )
            ELSE mejor_racha 
        END,
        
        ultima_fecha_jugada = date('now')
    WHERE username = NEW.username;
END;