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
1. As the Administrator I want to see the list of available sensors
2. As the Administrator I want to be notified of the warning status of a sensor
3. As the Administrator I want to filter sensors by name, type or status

### PORTS:
No ports open

### PERSISTANCE EVALUATION
The Ingestion Service container does not require data persistence as it works as a statless data pipeline that tranforms and forward data.

### EXTERNAL SERVICES CONNECTIONS
The Ingestion Service container connects to:
- The simulator container at simulator:8080 trough REST API and Websocket API
- The RabbitMQ container to broadcast data

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
	aihttp -> to be able to retrieve data via REST API asynchronously
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
	"timestamp": timestamp,
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

### USER STORIES:
1. As the Administrator I want to see current rules
2. As the Administrator I want to see the list of available actuators    
3. As the Administrator I want to add a rule
4. As the Administrator I want to remove a rule
5. As the Administrator I want to temporarily enable or disable a rule
6. As the Administrator I want my changes to be persistent
7. As the Administrator I want to switch an actuator on or off manually
8. As the Administrator I want to see the history of triggered rules
9. As the Administrator I want to see the current status of all actuators
10. As the Administrator I want to be notified of the trigger of a rule

## CONTAINER_NAME: Presentation
### DESCRIPTION:
The Presentation container acts as a frontend API gateway for the browser to visualize the received data.

### USER STORIES:
1. As the Administrator I want to visualize the trends of the latest sensors values
2. As the Administrator I want to know the status of the operative system
3. As the Administrator I want to filter rules by name, sensor or actuator of the rule
4. As the Administrator I want to monitor the status of the habitat through the dashboard
5. As the Administrator I want to see detailed information about a sensor
6. As the Administrator I want to navigate between interfaces intuitively

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
	- a thread that serves the html templates to the browser
- PAGES:

| Name                  | Description                     | Related Microservice | User Stories |
| --------------------- | ------------------------------- | -------------------- | ------------ |
| index.html            | Main dashboard                  | RabbitMQ             | TODO         |
| rules.html            | Rules management                | Processing Engine    |              |
| sensor_actuators.html | Sensor and actuators management | Processing Engine    |              |
| history.html          | Rules history                   | Processing Engine    |              |
