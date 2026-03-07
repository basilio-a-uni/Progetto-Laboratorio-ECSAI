from collections import defaultdict
import sqlite3
import os

class Rule():
    def __init__(self, row):
        # Gli indici sono slittati di 1 perché row[0] ora è l'ID
        self.id = row[0]
        self.sensor_name = row[1]
        self.metric = row[2]
        self.operator = row[3]
        self.sensor_target_value = row[4]
        self.actuator_name = row[5]
        self.actuator_set_value = row[6]
        self.enabled = bool(row[7]) # Rinominato in 'enabled'

    def is_not_respected(self, value):
        if self.operator == ">":
            return value > self.sensor_target_value
        elif self.operator == ">=":
            return value >= self.sensor_target_value
        elif self.operator == "=":
            return value == self.sensor_target_value
        elif self.operator == "<=":
            return value <= self.sensor_target_value
        elif self.operator == "<":
            return value < self.sensor_target_value
        else:
            raise ValueError(f"Operator '{self.operator}' is not a valid operator for a rule")

class State():
    # Sistemato l'init per evitare la mutabilità dei default di Python (defaultdict e dict vuoti)
    def __init__(self, sensor_data=None, current_rules=None, current_actuators_status=None):
        self.sensor_data = sensor_data or {}
        self.current_rules = current_rules or defaultdict(list)
        self.current_actuators_status = current_actuators_status or {}

    def load_persistent_rules(self):
        conn = sqlite3.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        cur.execute("SELECT * FROM rules")
        rows = cur.fetchall()
        for row in rows:
            rule = Rule(row)
            self.current_rules[rule.sensor_name].append(rule)
        conn.close()
    
    def load_persistent_actuators(self):
        self.current_actuators_status = {
            "cooling_fan": "OFF",
            "entrance_humidifier": "OFF",
            "hall_ventilation": "OFF",
            "habitat_heater": "OFF"
        }

    def create_new_rule(self, rule_data):
        conn = sqlite3.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()

        # Inseriamo i dati senza l'ID (lo genera SQLite con AUTOINCREMENT)
        cur.execute("""
            INSERT INTO rules (sensor_name, metric, operator, sensor_target_value, actuator_name, actuator_set_value, enabled) 
            VALUES(?, ?, ?, ?, ?, ?, ?)
        """, (rule_data['sensor_name'], rule_data['metric'], rule_data['operator'], 
              rule_data['sensor_target_value'], rule_data['actuator_name'], 
              rule_data['actuator_set_value'], True))
        
        # Prendiamo l'ID appena generato
        new_id = cur.lastrowid
        conn.commit()
        conn.close()

        # Ricreiamo la riga per istanziare l'oggetto Rule
        row = (new_id, rule_data['sensor_name'], rule_data['metric'], rule_data['operator'], 
               rule_data['sensor_target_value'], rule_data['actuator_name'], rule_data['actuator_set_value'], True)
        new_rule = Rule(row)
        self.current_rules[new_rule.sensor_name].append(new_rule)

    # NUOVO: Cancella una regola dal DB e dalla memoria
    def delete_rule(self, rule_id):
        conn = sqlite3.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        cur.execute("DELETE FROM rules WHERE id = ?", (rule_id,))
        conn.commit()
        conn.close()

        for sensor_name, rules in self.current_rules.items():
            self.current_rules[sensor_name] = [r for r in rules if r.id != rule_id]

    # NUOVO: Abilita/Disabilita la regola nel DB e nella memoria
    def toggle_rule(self, rule_id, is_enabled):
        conn = sqlite3.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        cur.execute("UPDATE rules SET enabled = ? WHERE id = ?", (is_enabled, rule_id))
        conn.commit()
        conn.close()

        for sensor_name, rules in self.current_rules.items():
            for r in rules:
                if r.id == rule_id:
                    r.enabled = is_enabled

    def get_rules_about(self, string):
        return self.current_rules[string]

    def update(self, data):
        source_id = data.get("source_id")
        if not source_id: return
        
        rules_to_check = self.get_rules_about(source_id)
        for rule in rules_to_check:
            if not rule.enabled:
                continue
            for metric in data.get("metrics", []):
                if rule.metric == metric["name"] and rule.is_not_respected(metric["value"]):
                    if self.current_actuators_status.get(rule.actuator_name) != rule.actuator_set_value:
                        # Sistemata formattazione stringa per evitare conflitti con gli apici
                        print(f"[Broken rule] Source: {rule.sensor_name}, metric: {rule.metric}, value: {metric['value']} (should not be {rule.operator}{rule.sensor_target_value}), setting {rule.actuator_name} to {rule.actuator_set_value}")
                        self.current_actuators_status[rule.actuator_name] = rule.actuator_set_value
                    else:
                        print("[Broken rule] Actuator was already to set value")