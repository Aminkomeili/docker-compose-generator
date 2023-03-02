import yaml
import docker
import re


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
    client = docker.from_env()
    # Run command in container
    container = client.containers.get(container)
    container.start()
    result = container.exec_run(command)
    container.stop()
    return result.output.decode('utf-8')


def parse_ping_output(output):
    # Extract transmitted, received and packet loss percentage
    match = re.search(r'(\d+) packets transmitted, (\d+) received, (\d+)% packet loss, time \d+ms', output)
    if match:
        transmitted, received, packet_loss_percent = match.groups()
    else:
        transmitted, received, packet_loss_percent = None, None, None

    # Extract min, avg, max and mdev RTT values
    rtt_data = re.findall(r'rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms', output)
    if rtt_data:
        rtt_min, rtt_avg, rtt_max, rtt_mdev = rtt_data[0]
    else:
        rtt_min, rtt_avg, rtt_max, rtt_mdev = None, None, None, None

    # Return parsed values as a dictionary
    return {
        'transmitted': int(transmitted),
        'received': int(received),
        'packet_loss_percent': int(packet_loss_percent),
        'rtt_min': float(rtt_min) if rtt_min is not None else None,
        'rtt_avg': float(rtt_avg) if rtt_avg is not None else None,
        'rtt_max': float(rtt_max) if rtt_max is not None else None,
        'rtt_mdev': float(rtt_mdev) if rtt_mdev is not None else None,
    }


def parse_tracepath_output(output):
    hop_pattern = r'(\d+):\s+([^\s]+)\s+(.*)\s+([\d.]+)ms(?:\s+pmtu\s+(\d+))?'
    hops = []
    for match in re.findall(hop_pattern, output):
        hop_data = {
            'hop_number': int(match[0]),
            'address': match[1],
            'hostname': match[2],
            'rtt': float(match[3]),
        }
        if match[4]:
            hop_data['pmtu'] = int(match[4])
        hops.append(hop_data)
    return hops


# #Test Code
# if __name__ == '__main__':
#     host1 = Host(
#         name="host1",
#         networks=[
#             Network(name="net1", subnet="10.0.1.0/24", intf="10.0.1.1", gateway='10.0.1.100'),
#             Network(name="net2", subnet="10.0.2.0/24", intf="10.0.2.1", gateway='10.0.2.100'),
#         ]
#     )
#     host2 = Host(
#         name="host2",
#         networks=[
#             Network(name="net1", subnet="10.0.1.0/24", intf="10.0.1.2", gateway="10.0.1.100"),
#             Network(name="net3", subnet="10.0.3.0/24", intf="10.0.3.1", gateway="10.0.3.100"),
#         ]
#     )
#
#     docker_compose = generate_docker_compose([host1, host2])
#
#     with open("docker-compose.yml", "w") as file:
#         yaml.dump(docker_compose, file)
#
#     result_c = run_command('docker-compose-generator_host2_1', "ping -c 4 10.0.1.2")
#     result_d = run_command('docker-compose-generator_host1_1', "echo Hello World")
#     print(result_c, result_d)
#     with open("result.txt", "w") as f:
#         f.write(result_c)
#         f.write(result_d)
