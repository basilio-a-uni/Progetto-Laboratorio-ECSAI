import sqlite3
import os

def init_db():
	conn = sqlite3.connect(os.getenv("DATABASE_URL"))

	cur = conn.cursor()

	cur.execute("""
	CREATE TABLE IF NOT EXISTS rules(
		sensor_name string,
		metric string,
		operator string CHECK(operator IN ('>', '>=', '=', '<=', '<')),
		sensor_target_value int,
		actuator_name string,
		actuator_set_value string CHECK(actuator_set_value IN ("ON", "OFF")),
		enabled bool
	)
	""")

	cur.execute("INSERT INTO rules VALUES('greenhouse_temperature', 'temperature_c', '>', 28, 'cooling_fan', 'ON', true)")

	cur.execute("SELECT * FROM rules")

	print(cur.fetchall())

	conn.commit()
	cur.close()
	conn.close()
