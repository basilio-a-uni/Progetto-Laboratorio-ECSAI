import sqlite3
import os

def init_db():
    conn = sqlite3.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()

    # AGGIUNTO: id INTEGER PRIMARY KEY AUTOINCREMENT
    cur.execute("""
    CREATE TABLE IF NOT EXISTS rules(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sensor_name TEXT,
        metric TEXT,
        operator TEXT CHECK(operator IN ('>', '>=', '=', '<=', '<')),
        sensor_target_value REAL,
        actuator_name TEXT,
        actuator_set_value TEXT CHECK(actuator_set_value IN ('ON', 'OFF')),
        enabled BOOLEAN
    )
    """)

    # Inseriamo la regola di default solo se la tabella è vuota
    cur.execute("SELECT COUNT(*) FROM rules")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO rules (sensor_name, metric, operator, sensor_target_value, actuator_name, actuator_set_value, enabled) 
            VALUES('greenhouse_temperature', 'temperature_c', '>', 0, 'cooling_fan', 'ON', 1)
        """)

    conn.commit()
    cur.close()
    conn.close()