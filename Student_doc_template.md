# SYSTEM DESCRIPTION:

Mars Base Operations is a centralized monitoring and control platform for Martian habitats. The system allows administrators to manage environmental telemetry in real time, control critical actuators, and define automation rules to ensure the safety of the base.

# USER STORIES:

1. As the Administrator I want to see current rules
2. As the Administrator I want to see the list of available actuators
3. As the Administrator I want to see the list of available sensors
4. As the Administrator I want to visualize the trends of the latest sensors values (piccolo fix todo: fare in modo che per le metriche con più di un valore il grafico mostra tutti i valori)
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
Manages all functionalities on the ingestion of data of different standards

### USER STORIES:
<list of user stories satisfied>

### PORTS: 
<used ports>

### DESCRIPTION:
<description of the container>

### PERSISTENCE EVALUATION
<description on the persistence of data>

### EXTERNAL SERVICES CONNECTIONS
<description on the connections to external services>

### MICROSERVICES:

#### MICROSERVICE: <name of the microservice>
- TYPE: backend
- DESCRIPTION: <description of the microservice>
- PORTS: <ports to be published by the microservice>
- TECHNOLOGICAL SPECIFICATION:
<description of the technological aspect of the microservice>
- SERVICE ARCHITECTURE: 
<description of the architecture of the microservice>

- ENDPOINTS: <put this bullet point only in the case of backend and fill the following table>
		
	| HTTP METHOD | URL | Description | User Stories |
	| ----------- | --- | ----------- | ------------ |
    | ... | ... | ... | ... |

- PAGES: <put this bullet point only in the case of frontend and fill the following table>

	| Name | Description | Related Microservice | User Stories |
	| ---- | ----------- | -------------------- | ------------ |
	| ... | ... | ... | ... |

- DB STRUCTURE: <put this bullet point only in the case a DB is used in the microservice and specify the structure of the tables and columns>

	**_<name of the table>_** :	| **_id_** | <other columns>

#### <other microservices>

## <other containers>
