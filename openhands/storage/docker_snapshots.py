#!/usr/bin/env python3
"""
## Test case ##

# Init docker-snapshots
cd /workspaces/OpenHands/openhands/storage/
./docker_snapshots.py enable

# Create test container
CONTAINER_ID=$(sudo docker run -d --name test-container ubuntu sleep infinity | tail -1)

# Register the new storage
./docker_snapshots.py register_new_subvolume --container $CONTAINER_ID

# Write test file
sudo docker exec $CONTAINER_ID touch /test

# Create snapshot (with test file)
SNAPSHOT_ID=$(./docker_snapshots.py create_snapshot --container $CONTAINER_ID | tail -1)

# Remove test file
sudo docker exec $CONTAINER_ID rm /test

# Restore snapshot
./docker_snapshots.py restore_snapshot --container $CONTAINER_ID --snapshot $SNAPSHOT_ID

# Check test file
sudo docker exec $CONTAINER_ID ls /test

# Remove test container
docker stop $CONTAINER_ID
docker rm $CONTAINER_ID
./docker_snapshots.py remove_container_snapshots --container $CONTAINER_ID

# Disable (revert changes)
./docker_snapshots.py disable

# Clear image and config
sudo pkill dockerd
rm /etc/docker/daemon.json
rm /var/lib/docker-snapshots.img
umount /var/lib/docker
"""
import os
import subprocess
import json
import argparse
import shlex
from datetime import datetime

LOOP_IMAGE = "/var/lib/docker-snapshots.img"
safe_loop_img = shlex.quote(LOOP_IMAGE)

def run_command(command, capture_output=False, throw_error=True):
    result = subprocess.run(command, shell=True, text=True, capture_output=capture_output)
    if throw_error and result.returncode != 0:
        raise RuntimeError(f"Command failed: {command}\nError: {result.stderr}")
    return result.stdout.strip() if capture_output else None

def enable():
    init_loop_image()
    configure_docker(True)
    print("Docker snapshots enabled.")

def disable():
    configure_docker(False)
    print("Docker snapshots disabled.")

def init_loop_image():
    if not os.path.exists(LOOP_IMAGE):
        print(f"Initializing Docker Btrfs loop image {LOOP_IMAGE}")
        run_command("sudo apt-get install -y btrfs-progs")
        run_command(f"sudo truncate -s 10G {safe_loop_img}")

def configure_docker(enable):
    changed = False
    file_path = "/etc/docker/daemon.json"

    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
    else:
        data = {}

    if enable:
        data["storage-driver"] = "btrfs"
        changed = True
    elif "storage-driver" in data:
        changed = True
        del data["storage-driver"]
    
    if changed:
        # Save config
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)

        docker_restart(enable)

    elif enable and not is_mounted():
        docker_restart(enable)

def mount_btrfs_storage():
    if not is_mounted():
        print("Mounting Btrfs storage...")
        loop_dev = run_command("losetup -f", capture_output=True)
        safe_loop_dev = shlex.quote(loop_dev)
        run_command(f"sudo losetup {safe_loop_dev} {safe_loop_img}")
        run_command(f"sudo mkfs.btrfs -f {safe_loop_dev}")
        os.makedirs("/var/lib/docker", exist_ok=True)
        run_command(f"sudo mount {safe_loop_dev} /var/lib/docker")
    else:
        print("Btrfs storage already mounted.")

def is_mounted():
    return bool(run_command('mount | grep "/var/lib/docker type btrfs"', capture_output=True, throw_error=False))

def docker_restart(enabled):
    print("Restarting Docker daemon")

    # Stop
    run_command("sudo pkill dockerd || true")
    run_command("sleep 1")

    if enabled:
        mount_btrfs_storage()

    # Start
    run_command("sudo dockerd --pidfile=/var/run/docker.pid > /dev/null 2>&1 &")

def restart_container(container_id):
    if not container_id: raise ValueError("Missing container_id")
    run_command(f"docker restart {container_id}")
    
def get_storage(container_id):
    storage_path_file = f"/var/lib/docker/btrfs/snapshots/{container_id}/storage"
    safe_storage_path_file = shlex.quote(storage_path_file)
    storage_path = run_command(f"sudo cat {safe_storage_path_file}", capture_output=True, throw_error=False).strip()
    if not storage_path:
        print("WARNING: Couldn't get container storage path: register_new_subvolume() was not called after the container creation.")
        return None
    return "/var/lib/docker/" + storage_path

def create_snapshot(container_id):
    if not container_id: raise ValueError("Missing container_id")
    snapshot_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    storage_path = get_storage(container_id)
    if not storage_path: return
    safe_storage_path = shlex.quote(storage_path)
    snapshot_path = shlex.quote(f"/var/lib/docker/btrfs/snapshots/{container_id}/{snapshot_id}")
    run_command(f"sudo btrfs subvolume snapshot {safe_storage_path} {snapshot_path}")
    return snapshot_id

def restore_snapshot(container_id, snapshot_id):
    if not container_id: raise ValueError("Missing container_id")
    if not snapshot_id: raise ValueError("Missing snapshot_id")
    storage_path = get_storage(container_id)
    if not storage_path: return
    safe_storage_path = shlex.quote(storage_path)
    snapshot_path = shlex.quote(f"/var/lib/docker/btrfs/snapshots/{container_id}/{snapshot_id}")
    run_command(f"sudo btrfs subvolume delete {safe_storage_path}", False, False)
    run_command(f"sudo btrfs subvolume snapshot {snapshot_path} {safe_storage_path}")
    restart_container(container_id)

def register_new_subvolume(container_id):
    """
    Since there is no easy way to obtain the underlying btrfs storage path by container_id
    we will register it when a new container is created.
    """
    if not container_id: raise ValueError("Missing container_id")
    snapshots_path = f"/var/lib/docker/btrfs/snapshots/{container_id}"
    os.makedirs(snapshots_path, exist_ok=True)
    subvolume_path = run_command("sudo btrfs subvolume list -p /var/lib/docker/btrfs | tail -n 1 | awk '{print $NF}'", capture_output=True)
    with open(f"{snapshots_path}/storage", "w") as storage_file:
        storage_file.write(subvolume_path)

def sudo_command(args):
    subprocess.check_call(['sudo', __file__, *args])

def remove_container_snapshots(container_id):
    if not container_id: raise ValueError("Missing container_id")
    run_command(f"rm -rf /var/lib/docker/btrfs/snapshots/{container_id}")

def main():
    parser = argparse.ArgumentParser(description="Docker Snapshot Management")
    parser.add_argument("command", help="Command to execute", choices=[
        "enable",
        "disable",
        "create_snapshot",
        "restore_snapshot",
        "register_new_subvolume",
        "remove_container_snapshots",
        "restart_container"])
    parser.add_argument("--container", help="Container ID")
    parser.add_argument("--snapshot", help="Snapshot ID")
    args = parser.parse_args()

    try:
        if args.command == "enable":
            enable()
        elif args.command == "disable":
            disable()
        elif args.command == "create_snapshot":
            create_snapshot(args.container)
        elif args.command == "restore_snapshot":
            restore_snapshot(args.container, args.snapshot)
        elif args.command == "register_new_subvolume":
            register_new_subvolume(args.container)
        elif args.command == "remove_container_snapshots":
            remove_container_snapshots(args.container)
        elif args.command == "restart_container":
            restart_container(args.container)
        else:
            print("Unknown command")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
