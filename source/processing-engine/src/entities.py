from collections import defaultdict
import sqlite3
import os

class Rule():
    def __init__(self, row):
        self.sensor_name = row[0]
        self.metric = row[1]
        self.operator = row[2]
        self.sensor_target_value = row[3]
        self.actuator_name = row[4]
        self.actuator_set_value = row[5]
        self.enable = bool(row[6])

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
    def __init__(self, sensor_data = {}, current_rules = defaultdict(list), current_actuators_status = {}):
        self.sensor_data = sensor_data
        self.current_rules = current_rules
        self.current_actuators_status = current_actuators_status

    def load_persistent_rules(self):
        conn = sqlite3.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()

        cur.execute("SELECT * FROM rules")
        rows = cur.fetchall()

        for row in rows:
            self.current_rules[row[0]].append(Rule(row))
    
    def load_persistent_actuators(self):
        # temporary TODO (maybe?): add persistance to actuators
        self.current_actuators_status = {
            "cooling_fan": "OFF",
            "entrance_humidifier": "OFF",
            "hall_ventilation": "OFF",
            "habitat_heater": "OFF"
        }

    def create_new_rule(self, rule):
        conn = sqlite3.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()

        cur.execute("INSERT INTO rules VALUES(?, ?, ?, ?, ?, ?, ?)",
                (self.sensor_name, self.metric, self.operator, self.sensor_target_value,
                self.actuator_name, self.actuator_set_value, self.enable)
            )
        conn.commit()
        cur.close()
        conn.close()

        self.current_rules[self.sensor_name].append(rule)


    def get_rules_about(self, string):
        return self.current_rules[string]

    def update(self, data):
        source_id = data["source_id"]
        rules_to_check = self.get_rules_about(source_id)
        for rule in rules_to_check:
            for metric in data["metrics"]:
                if not rule.enable:
                    continue
                if rule.metric == metric["name"] and rule.is_not_respected(metric["value"]):
                    if self.current_actuators_status[rule.actuator_name] != rule.actuator_set_value:
                        print(f"[Broken rule] Source: {rule.sensor_name}, metric: {rule.metric}, value: {metric["value"]} (should be {rule.operator}{rule.sensor_target_value}), setting {rule.actuator_name} to {rule.actuator_set_value}")
                        self.current_actuators_status[rule.actuator_name] = rule.actuator_set_value
                    else:
                        print(f"[Broken rule] Actuator was already to set value")
