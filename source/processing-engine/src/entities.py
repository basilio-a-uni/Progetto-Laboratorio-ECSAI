from collections import defaultdict
import sqlite3
import os
import time

class Rule():
    def __init__(self, data):
        print(data)
        if type(data) == list or type(data) == tuple:
            self.id = data[0]
            self.sensor_name = data[1]
            self.metric = data[2]
            self.operator = data[3]
            self.sensor_target_value = data[4]
            self.actuator_name = data[5]
            self.actuator_set_value = data[6]
            self.enabled = bool(data[7])
        elif type(data) == dict:
            self.id = data['id']
            self.sensor_name = data['sensor_name']
            self.metric = data['metric'] 
            self.operator = data['operator']
            self.sensor_target_value = data['sensor_target_value']
            self.actuator_name = data['actuator_name']
            self.actuator_set_value = data['actuator_set_value']
            self.enabled = bool(data["enabled"])

    def is_not_respected(self, value):
        if self.operator == ">":
            return value > self.sensor_target_value
        elif self.operator == ">=":
            return value >= self.sensor_target_value
        elif self.operator == "==":
            return value == self.sensor_target_value
        elif self.operator == "<=":
            return value <= self.sensor_target_value
        elif self.operator == "<":
            return value < self.sensor_target_value
        else:
            raise ValueError(f"Operator '{self.operator}' is not a valid operator for a rule")


class State():
    def __init__(self, sensor_data=None, current_rules=None, triggered_rules_history=None, current_actuators_status=None, on_actuator_change=None, on_rule_triggered=None):
        self.sensor_data = sensor_data or {}
        self.current_rules = current_rules or defaultdict(list)
        self.triggered_rules_history = triggered_rules_history or {}
        self.current_actuators_status = current_actuators_status or {}
        self.on_actuator_change = on_actuator_change
        self.on_rule_triggered = on_rule_triggered

    def load_persistent_rules(self):
        conn = sqlite3.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()

        cur.execute("SELECT * FROM rules")
        rows = cur.fetchall()
        self.current_rules = defaultdict(list)
        for row in rows:
            self.current_rules[row[1]].append(Rule(row))
    
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

        cur.execute("""
            INSERT INTO rules (sensor_name, metric, operator, sensor_target_value, actuator_name, actuator_set_value, enabled) 
            VALUES(?, ?, ?, ?, ?, ?, ?)
        """, (rule_data['sensor_name'], rule_data['metric'], rule_data['operator'], 
              rule_data['sensor_target_value'], rule_data['actuator_name'], 
              rule_data['actuator_set_value'], True))

        new_id = cur.lastrowid

        conn.commit()
        cur.close()
        conn.close()

        rule_data['id'] = new_id
        rule_data['enabled'] = True
        new_rule = Rule(rule_data)
        self.current_rules[new_rule.sensor_name].append(new_rule)        

    def delete_rule(self, rule_id):
        conn = sqlite3.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        cur.execute("DELETE FROM rules WHERE id = ?", (rule_id,))
        conn.commit()
        conn.close()

        for sensor_name, rules in self.current_rules.items():
            self.current_rules[sensor_name] = [r for r in rules if r.id != rule_id]

    def update_rule(self, rule_data):
        conn = sqlite3.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()

        cur.execute("""
            UPDATE rules
            SET sensor_name=?, metric=?, operator=?, sensor_target_value=?, actuator_name=?, actuator_set_value=?, enabled=?
            WHERE id=?
        """, (rule_data['sensor_name'], rule_data['metric'], rule_data['operator'], 
              rule_data['sensor_target_value'], rule_data['actuator_name'], 
              rule_data['actuator_set_value'], rule_data['enabled'], rule_data['id']
            )
        )
        conn.commit()
        conn.close()

        self.load_persistent_rules()

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

        self.sensor_data[source_id] = data

        rules_to_check = self.get_rules_about(source_id)
        for rule in rules_to_check:
            if not rule.enabled:
                continue

            for metric in data.get("metrics", []):
                if metric["name"] != rule.metric:
                    continue
                if rule.is_not_respected(metric["value"]):
                    if self.current_actuators_status.get(rule.actuator_name) != rule.actuator_set_value:
                        self.triggered_rules_history[rule.id] = {"triggered_at": time.time(), "last_trigger_value": metric["value"]}
                        print(f"[Triggered rule] Source: {rule.sensor_name}, metric: {rule.metric}, value: {metric['value']} (should not be {rule.operator}{rule.sensor_target_value}), setting {rule.actuator_name} to {rule.actuator_set_value}")
                        self.current_actuators_status[rule.actuator_name] = rule.actuator_set_value
                        
                        if self.on_rule_triggered:
                            self.on_rule_triggered(rule, metric["value"])

                        if self.on_actuator_change:
                            self.on_actuator_change(rule.actuator_name, rule.actuator_set_value)
                    else:
                        self.triggered_rules_history[rule.id] = {"triggered_at": time.time(), "last_trigger_value": metric["value"]}
                        print("[Triggered rule] Actuator was already to set value")
