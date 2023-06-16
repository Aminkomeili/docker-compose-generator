"""
Author: Amin komeili
Date: 2023-03-15
"""
import re
import yaml
import os
import docker



class Network:
    def __init__(self, name, subnet, intf, gateway):
        """
                :param name: نام شبکه
                :param subnet: Subnet شبکه
                :param intf: آدرس IP اینترفیس شبکه برای این Host
                :param gateway: IP Gateway برای Subnet شبکه
                """
        self.name = name
        self.subnet = subnet
        self.intf = intf
        self.gateway = gateway


class Host:
    def __init__(self, name, networks, command="tail -f /dev/null"):
        """
               :param name: نام Host
               :param networks: لیست شبکه هایی که Host به آن متصل است
               """
        self.name = name
        self.networks = networks
        self.command = command

    def to_dict(self):
        """
               تبدیل اطلاعات Host به فرمت dictionary برای استفاده در فایل Docker Compose

               :return: دیکشنری حاوی اطلاعات Host
               """
        networks_dict = {}
        for network in self.networks:
            networks_dict[network.name] = {
                "ipv4_address": network.intf,
            }

        return {
            "version": "2.4",
            "services": {
                self.name: {
                    "container_name": self.name,
                    "image": "alpine",
                    "command": 'tail -f /dev/null',
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

    def run_command(self):
        """
            اجرای دستور داخل یک container و بازگرداندن output آن

            :param container: نام container
            :param command: دستوری که باید اجرا شود
            :return: خروجی دستور اجرا شده
            """
        client = docker.from_env()
        container = client.containers.get(self.name)
        container.start()
        result = container.exec_run(self.command)
        container.stop()
        return result.output.decode('utf-8')


def generate_docker_compose(hosts):
    """
        تبدیل اطلاعات تمامی Host ها به فرمت Docker Compose

        :param hosts: لیست هاست هایی که باید به فایل Docker Compose اضافه شوند
        :return: دیکشنری حاوی اطلاعات Docker Compose
        """
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


def parse_ping_output(output):
    match = re.search(r'(\d+) packets transmitted, (\d+) packets received, (\d+)% packet loss', output)
    if match:
        transmitted, received, packet_loss_percent = match.groups()
    else:
        transmitted, received, packet_loss_percent = None, None, None

    rtt_data = re.findall(r'round-trip min/avg/max = ([\d.]+)/([\d.]+)/([\d.]+) ms', output)
    if rtt_data:
        rtt_min, rtt_avg, rtt_max = rtt_data[0]
    else:
        rtt_min, rtt_avg, rtt_max = None, None, None

    return {
        'transmitted': int(transmitted),
        'received': int(received),
        'packet_loss_percent': str(packet_loss_percent),
        'rtt_min': float(rtt_min) if rtt_min is not None else None,
        'rtt_avg': float(rtt_avg) if rtt_avg is not None else None,
        'rtt_max': float(rtt_max) if rtt_max is not None else None,
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


# Test Code
if __name__ == '__main__':
    host1 = Host(
        name="host1",
        networks=[
            Network(name="net1", subnet="10.0.1.0/24", intf="10.0.1.1", gateway='10.0.1.100'),
            Network(name="net2", subnet="10.0.2.0/24", intf="10.0.2.1", gateway='10.0.2.100'),
        ], command="ping -c 4 1.1.1.1 "
    )
    host2 = Host(
        name="host2",
        networks=[
            Network(name="net1", subnet="10.0.1.0/24", intf="10.0.1.2", gateway="10.0.1.100"),
            Network(name="net3", subnet="10.0.3.0/24", intf="10.0.3.1", gateway="10.0.3.100"),
        ], command="ping -c 4 1.1.1.1"
    )

    docker_compose = generate_docker_compose([host1])

    with open("docker-compose.yml", "w") as file:
        yaml.dump(docker_compose, file)
    os.system("docker-compose up -d")
    rs1 = host1.run_command()
    # rs2 = host2.run_command()

    # print(rs1, rs2)
    print(parse_ping_output(rs1))
