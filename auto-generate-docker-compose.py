import yaml


class Network:
    def __init__(self, name, subnet, intf, gateway):
        self.name = name
        self.subnet = subnet
        self.intf = intf
        self.gateway = gateway


class Host:
    def __init__(self, name, networks):
        self.name = name
        self.networks = networks

    def to_dict(self):
        networks_dict = {}
        for network in self.networks:
            networks_dict[network.name] = {
                "ipv4_address": network.intf,
            }

        return {
            "version": "2.4",
            "services": {
                self.name: {
                    "image": "alpine",
                    "command": "tail -f /dev/null",
                    "tty": 'true',
                    "networks": networks_dict
                }
            },
            "networks": {
                network.name: {
                    "driver": "bridge",
                    "ipam": {
                        "config": [
                            {
                                "subnet": network.subnet,
                                "gateway": network.gateway
                            }
                        ]
                    }
                }
                for network in self.networks
            }
        }


def generate_docker_compose(hosts):
    services = {}
    networks = {}
    for host in hosts:
        services.update(host.to_dict()["services"])
        networks.update(host.to_dict()["networks"])

    return {
        "version": "2.4",
        "services": services,
        "networks": networks
    }


def run_command(container, command):
    import docker
    client = docker.from_env()
    # Run command in container
    container = client.containers.get(container)
    container.start()
    result = container.exec_run(command)
    container.stop()
    return result.output.decode('utf-8')


if __name__ == '__main__':
    host1 = Host(
        name="host1",
        networks=[
            Network(name="net1", subnet="10.0.1.0/24", intf="10.0.1.1", gateway='10.0.1.100'),
            Network(name="net2", subnet="10.0.2.0/24", intf="10.0.2.1", gateway='10.0.2.100'),
        ]
    )
    host2 = Host(
        name="host2",
        networks=[
            Network(name="net1", subnet="10.0.1.0/24", intf="10.0.1.2", gateway="10.0.1.100"),
            Network(name="net3", subnet="10.0.3.0/24", intf="10.0.3.1", gateway="10.0.3.100"),
        ]
    )

    docker_compose = generate_docker_compose([host1, host2])

    with open("docker-compose.yml", "w") as file:
        yaml.dump(docker_compose, file)

    result_c = run_command('dockerclient_host2_1', "ping -c 4 10.0.1.2")
    result_d = run_command('dockerclient_host1_1', "echo Hello World")
    print(result_c, result_d)
    with open("result.txt", "w") as f:
        f.write(result_c)
        f.write(result_d)
