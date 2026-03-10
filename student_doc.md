# SYSTEM DESCRIPTION:

Mars Base Operations is a centralized monitoring and control platform for Martian habitats. The system allows administrators to manage environmental telemetry in real time, control critical actuators, and define automation rules to ensure the safety of the base.

# USER STORIES:

1. As the Administrator I want to see current rules
2. As the Administrator I want to see the list of available actuators
3. As the Administrator I want to see the list of available sensors
4. As the Administrator I want to visualize the trends of the latest sensors values
5. As the Administrator I want to know the status of the operative system
6. As the Administrator I want to add a rule
7. As the Administrator I want to remove a rule
8. As the Administrator I want to modify a rule 
9. As the Administrator I want to temporarily enable or disable a rule
10. As the Administrator I want to filter rules by name, sensor or actuator of the rule
11. As the Administrator I want my changes to be persistent
12. As the Administrator I want to be notified of the warning status of a sensor 
13. As the Administrator I want to monitor the status of the habitat through the dashboard 
14. As the Administrator I want to switch an actuator on or off manually
15. As the Administrator I want to see the history of triggered rules
16. As the Administrator I want to filter sensors by name, type or status
17. As the Administrator I want to see detailed information (name, type, latest status and description) about a sensor
18. As the Administrator I want to see the current status of all actuators
19. As the Administrator I want to navigate between interfaces intuitively 
20. As the Administrator I want to be notified of the trigger of a rule


# CONTAINERS:

## CONTAINER_NAME: Ingestion Service

### DESCRIPTION: 
The ingestion service receives data from the REST sensors and the telemetry stream, to unify and centralize them.

### USER STORIES:
3 As the Administrator I want to see the list of available sensors
12 As the Administrator I want to be notified of the warning status of a sensor
16 As the Administrator I want to filter sensors by name, type or status

### PORTS:
No ports open

### PERSISTANCE EVALUATION
The Ingestion Service container does not require data persistence as it works as a statless data pipeline that tranforms and forward data.

### EXTERNAL SERVICES CONNECTIONS
The Ingestion Service container connects to:
- The simulator container at simulator:8080 trough REST API and Websocket API
- The RabbitMQ container to broadcast data via the pika library

### MICROSERVICES:
#### MICROSERVICE: Ingestion Service
- TYPE: backend
- DESCRIPTION: The ingestion service receives data from the REST sensors and the telemetry stream, to unify and centralize them.
- PORTS: No open ports
- TECHNOLOGICAL SPECIFICATION:
The microservices utilizes the Python programming language, specifically targeting python 3.12.
The service is build using the following key packages:
	asyncio -> to be able to poll all sensor at the same time on the same thread instead of using the more heavy approach of multithreading
	websockets -> to be able to retrieve data via Websocket API
	aiohttp -> to be able to retrieve data via REST API asynchronously
	pika -> to be able to connect to the RabbitMQ container
- SERVICE ARCHITECTURE:
The service is realized with:
	- a function to easily broadcast data
	- a function that unify the data in a unique event data JSON schema
	- a coroutine that polls the REST API of a sensor every 5 seconds
	- a coroutine that receive all the data of a topic via Websocket API

- EVENT SCHEMA:
```json
{
	"source_id": "sensor/telemetry name",
	"source_type": "telemetry"/"rest",
	"timestamp": "timestamp",
	"status": "ok"/"warning",
	"metrics": [
		{
			"name": "metric name",
			"value": "value for that metric",
			"unit": "unit of measurement for that metric"
		}
	]
}
```

## CONTAINER_NAME: Processing Engine
### DESCRIPTION:
The processing engine receives data from the ingestion engine and process it to see if any sensor break any rules and applies the changes to the actuators.

### USER STORIES:
1 As the Administrator I want to see current rules
2 As the Administrator I want to see the list of available actuators    
6 As the Administrator I want to add a rule
7 As the Administrator I want to remove a rule
8 As the Administrator I want to modify a rule 
9 As the Administrator I want to temporarily enable or disable a rule
11 As the Administrator I want my changes to be persistent
14 As the Administrator I want to switch an actuator on or off manually
18 As the Administrator I want to see the current status of all actuators
20 As the Administrator I want to be notified of the trigger of a rule

### PORTS
8001:8001

### PERSISTANCE EVALUATION
The Processing Engine container does need persistance data to store the rules.
We'll use SQLite since it's embedded and don't need an external container to work

### EXTERNAL SERVICES CONNECTIONS
The Processing Engine container connects to:
- RabbitMQ container to receive data from the ingestion service

### MICROSERVICES:
#### MICROSERVICE: Processing Engine
- TYPE: backend
- DESCRIPTION: The processing engine receives data from the ingestion engine and process it to see if any sensor break any rules and applies the changes to the actuators.
- PORTS: 8001
- TECHNOLOGICAL SPECIFICATION:
The microservices utilizes the Python programming language, specifically targeting python 3.12.
The service is build using the following key packages:
	pika -> to be able to connect to the RabbitMQ container
	flask -> to be able to send data to the Presentation container
	threading -> to be able to run both the flask app and the RabbitMQ receiver
	sqlite3 -> to manage persistency for rules
- SERVICE ARCHITECTURE:
The service is realized with:
	- two classes State and Rule that acts as a cache
	- a thread that receive the data from the ingestion engine and analyze it with current rules
	- a thread that acts as a backend for the Presentation container 
- ENDPOINTS:

| HTTP METHOD | URL                             | Description                        | User Stories |
| ----------- | ------------------------------- | ---------------------------------- | ------------ |
| GET         | /rules                          | Get a list of rules                | 1            |
| POST        | /rules                          | Add a rule                         | 6            |
| DELETE      | /rules/<int:rule_id>            | Delete a rule                      | 7            |
| POST        | /rules/update                   | Update a rule                      | 8            |
| POST        | /rules/<int:rule_id>/toggle     | Toggle on or off a rule            | 9            |
| GET         | /history                        | Get the history of triggered rules |              |
| GET         | /sensors                        | Get last data about the sensors    |              |
| GET         | /actuators                      | Get last data about the actuators  | 2, 18        |
| POST        | /actuators/<actuator_id>/toggle | Toggle on or off an actuator       | 14           |
| GET         | /telemetry/latest               | Get all the data about the sensors | 20           |

- DB STRUCTURE:
***Rules***: | ***id*** | sensor_name | metric | operator | sensor_target_value | actuator_name | actuator_set_value | enabled


## CONTAINER_NAME: Presentation
### DESCRIPTION:
The Presentation container acts as a frontend API gateway for the browser to visualize the received data.

### USER STORIES:
4 As the Administrator I want to visualize the trends of the latest sensors values
5 As the Administrator I want to know the status of the operative system
10 As the Administrator I want to filter rules by name, sensor or actuator of the rule
13 As the Administrator I want to monitor the status of the habitat through the dashboard
15 As the Administrator I want to see the history of triggered rules
17 As the Administrator I want to see detailed information about a sensor
19 As the Administrator I want to navigate between interfaces intuitively

### PORTS
8000:8000

### PERSISTANCE EVALUATION
The Presentation service does not requires persistent storage since it's juste a simple flask application that sends the html files to the browser

### EXTERNAL SERVICES CONNECTIONS
The Presentation container connects to:
- The RabbitMQ container to receive data from the ingestion service
- The Processing Engine container via rest polling to get information about rules and actuators

### MICROSERVICES
#### MICROSERVICE: Presentation
- TYPE: frontend
- DESCRIPTION: The Presentation container acts as a frontend API gateway for the browser to visualize the received data.
- PORTS: 8000
- TECHNOLOGICAL SPECIFICATION:
The microservices utilizes the Python programming language, specifically targeting python 3.12.
The service is build using the following key packages:
	pika -> to be able to connect to the RabbitMQ container and receive data directly from the ingestion engine
	requests and flask -> to be able to establish routes and comunicate with the Processing Engine container
- SERVICE ARCHITECTURE:
The service is realized with:
	- a thread that receives data from the ingestion service via the RabbitMQ container
	- a thread that serves the html templates to the browser with other infos 
- PAGES:

| Name                  | Description                     | Related Microservice | User Stories |
| --------------------- | ------------------------------- | -------------------- | ------------ |
| index.html            | Main dashboard                  | RabbitMQ             | 4, 5, 13     |
| rules.html            | Rules management                | Processing Engine    | 10           |
| sensor_actuators.html | Sensor and actuators management | Processing Engine    | 17           |
| history.html          | Rules history                   | Processing Engine    | 15           |
