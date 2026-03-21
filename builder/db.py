import sqlite3
def create_db():
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    conn.execute("PRAGMA foreign_keys = ON")
    # Tabla de perfiles
    try:
        with open("createdb.sql", "r") as f:

            c.executescript(f.read())

    except Exception as e:
        print("Error:", e)

    # Tabla de tiempos (la que ya tenías)
    conn.commit()
    conn.close()

create_db()
