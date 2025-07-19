import ipaddress
import subprocess

import docker

import netifaces

def get_default_ifname() -> str:
    """Return the iface that owns the IPv4 default route (e.g. 'enp39s0')."""
    return netifaces.gateways()['default'][netifaces.AF_INET][1]

SHIM_NAME    = "ipvlan-shim"
PARENT_IF    = get_default_ifname()
DRIVER       = "ipvlan"
MODE         = "l3"

client = docker.from_env()

def _run_cmd(cmd, check=False):
    """Run a shell command and raise if it fails."""
    subprocess.run(cmd, check=check, text=True)

def add_host_shim(subnet, name=SHIM_NAME):
    """
    Give the host an IP inside the macvlan subnet so it can reach containers.
    Creates an interface named 'mv-shim'.
    """
    shim_ip = list(ipaddress.ip_network(subnet))[1]  # pick .1 (usually gateway)
    while True:
        try:
            # This works on AWS.
            _run_cmd(["sudo", "ip", "link", "add", name, "link", PARENT_IF, "type", "ipvlan", "mode", "l3"])
            break
        except subprocess.CalledProcessError as e:
            # interface might already exist from a previous run

            # Remove the existing interface if it exists and retry.
            print("Trying to remove existing mv-shim interface...")
            _run_cmd(["sudo", "ip", "link", "del", "mv-shim"], check=False)
            continue

    _run_cmd(["sudo", "ip", "addr", "add", subnet, "dev", name])
    _run_cmd(["sudo", "ip", "link", "set", name, "up"])

def remove_host_shim(name=SHIM_NAME):
    try:
        _run_cmd(["sudo", "ip", "link", "del", name])
    except subprocess.CalledProcessError:
        pass  # already gone

def network_up(network_name, subnet):
    ipam_pool = docker.types.IPAMPool(subnet=subnet)
    ipam_cfg  = docker.types.IPAMConfig(pool_configs=[ipam_pool])

    net = client.networks.create(
        name=network_name,
        driver=DRIVER,
        ipam=ipam_cfg,
        options={"parent": PARENT_IF,
                 f"{DRIVER}_mode": MODE} if MODE else {"parent": PARENT_IF}
    )
    add_host_shim(subnet)
    print(f"✔ Network '{network_name}' created with subnet {subnet}")

def network_down(network_name):
    try:
        net = client.networks.get(network_name)
        net.remove()
        print(f"✔ Network '{network_name}' removed")
    except docker.errors.NotFound:
        print(f"✘ Network '{network_name}' not found")
    remove_host_shim()
    print("✔ Host shim removed")
