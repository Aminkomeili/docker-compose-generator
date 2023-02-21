# Docker Compose Generator

This is a Python script for generating a Docker Compose file that defines a network and a container. It defines two classes Network and Host for creating the network and the container, respectively.
Requirements

1. Python 3.5 or higher
2. Docker

## Installation

Clone this repository:

`git clone https://github.com/your-username/docker-compose-generator.git`

## Install the required packages:

` pip install -r requirements.txt`

## Usage
 Create a new Python script and import the Network, Host, and generate_docker_compose classes:
 
```
import docker
from docker_compose_generator import Network, Host, generate_docker_compose```
```
Define the network(s) and host(s) that you want to create using the Network and Host classes:

```
network1 = Network("network1", "10.0.1.0/24", "10.0.1.1", "10.0.1.254")
host1 = Host("host1", [network1])
```
Generate the Docker Compose file using the generate_docker_compose function:

`docker_compose = generate_docker_compose([host1])`


Save the Docker Compose file to disk:

```
with open("docker-compose.yml", "w") as f:
    f.write(yaml.dump(docker_compose))
```

Run the Docker Compose file using the docker-compose command:

`docker-compose up -d`

License

This project is licensed under the MIT License - see the LICENSE file for details.
