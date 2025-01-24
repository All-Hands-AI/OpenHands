#!/usr/bin/python3
"""
## Test case ##

# Init docker-snapshots
./docker-snapshots init_storage

# Create test container
CONTAINER_ID=$(sudo docker run -d --name test-container ubuntu sleep infinity | tail -1)

# Register the new storage
./docker-snapshots register_new_subvolume --container $CONTAINER_ID

# Write test file
sudo docker exec $CONTAINER_ID touch /test

# Create snapshot (with test file)
SNAPSHOT_ID=$(./docker-snapshots create_snapshot --container $CONTAINER_ID | tail -1)

# Remove test file
sudo docker exec $CONTAINER_ID rm /test

# Restore snapshot
./docker-snapshots restore_snapshot --container $CONTAINER_ID --snapshot $SNAPSHOT_ID

# Check test file
sudo docker exec $CONTAINER_ID ls /test

# Remove test container
docker stop test-container
docker rm test-container
./docker-snapshots remove_container_snapshots --container $CONTAINER_ID 
"""
import os
import subprocess
import json
import argparse
import shlex
from datetime import datetime

LOOP_IMAGE = "/var/lib/docker-snapshots.img"

def run_command(command, capture_output=False, throw_error=True):
	result = subprocess.run(command, shell=True, text=True, capture_output=capture_output)
	if throw_error and result.returncode != 0:
		raise RuntimeError(f"Command failed: {command}\nError: {result.stderr}")
	return result.stdout.strip() if capture_output else None

def init_storage():
	docker_init()
	docker_configure()
	print("Docker snapshots volume initialized.")

def docker_init():
	if not os.path.exists(LOOP_IMAGE):
		print(f"Initializing Docker snapshots loop image {LOOP_IMAGE}")
		run_command("sudo apt-get install -y btrfs-progs")
		run_command(f"sudo truncate -s 10G {LOOP_IMAGE}")
	mount_btrfs_storage()

def docker_configure():
	# TODO: Patch file content
	print("Setting up /etc/docker/daemon.json")
	os.makedirs("/etc/docker", exist_ok=True)
	with open("/etc/docker/daemon.json", "w") as daemon_file:
		json.dump({"storage-driver": "btrfs"}, daemon_file)

def mount_btrfs_storage():
	if not is_mounted():
		print("Mounting Btrfs storage...")
		loop_dev = run_command("losetup -f", capture_output=True)
		run_command(f"sudo losetup {loop_dev} {LOOP_IMAGE}")
		run_command(f"sudo mkfs.btrfs -f {loop_dev}")
		os.makedirs("/var/lib/docker", exist_ok=True)
		run_command(f"sudo mount {loop_dev} /var/lib/docker")
		docker_restart_daemon()
	else:
		print("Btrfs storage already mounted.")

def is_mounted():
	return bool(run_command('mount | grep "/var/lib/docker type btrfs"', capture_output=True, throw_error=False))

def docker_restart_daemon():
	print("Restarting Docker daemon")
	run_command("sudo pkill dockerd || true")
	run_command("sleep 1")
	run_command("sudo dockerd --pidfile=/var/run/docker.pid > docker.log 2>&1 &")

def restart_container(container_id):
	if not container_id: raise ValueError("container_id is not set")
	run_command(f"docker restart {container_id}")
	
def get_volume(container_id):
	storage_path_file = f"/var/lib/docker/btrfs/snapshots/{container_id}/storage"
	if not os.path.exists(storage_path_file):
		raise FileNotFoundError("Error: 'storage' file is missing. See: register_new_subvolume()")
	storage_path = open(storage_path_file).read().strip()
	if not storage_path: raise ValueError("Couldn't get the storage path.")
	return storage_path

def create_snapshot(container_id):
	if not container_id:
		raise ValueError("Missing --container")
	storage_path = "/var/lib/docker/" + get_volume(container_id)
	snapshot_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
	snapshot_path = f"/var/lib/docker/btrfs/snapshots/{container_id}/{snapshot_id}"
	run_command(f"sudo btrfs subvolume snapshot {storage_path} {snapshot_path}")
	print(snapshot_id)

def restore_snapshot(container_id, snapshot_id):
	if not container_id or not snapshot_id:
		raise ValueError("CONTAINER_ID and SNAPSHOT_ID must be set")
	vol = get_volume(container_id)
	storage_path = "/var/lib/docker/" + vol
	run_command(f"sudo btrfs subvolume delete {storage_path} || true")
	run_command(f"sudo btrfs subvolume snapshot /var/lib/docker/btrfs/snapshots/{container_id}/{snapshot_id} {storage_path}")
	restart_container(container_id)

def register_new_subvolume(container_id):
	if not container_id: raise ValueError("container_id is not set")
	snapshots_path = f"/var/lib/docker/btrfs/snapshots/{container_id}"
	os.makedirs(snapshots_path, exist_ok=True)
	subvolume_path = run_command("sudo btrfs subvolume list -p /var/lib/docker/btrfs | tail -n 1 | awk '{print $NF}'", capture_output=True)
	with open(f"{snapshots_path}/storage", "w") as storage_file:
		storage_file.write(subvolume_path)

def remove_container_snapshots(container_id):
	if not container_id: raise ValueError("container_id is not set")
	run_command(f"rm -rf /var/lib/docker/btrfs/snapshots/{container_id}")

def main():
	parser = argparse.ArgumentParser(description="Docker Snapshot Management")
	parser.add_argument("command", help="Command to execute", choices=[
		"init_storage",
		"create_snapshot",
		"restore_snapshot",
		"register_new_subvolume",
		"remove_container_snapshots",
		"restart_container"])
	parser.add_argument("--container", help="Container ID")
	parser.add_argument("--snapshot", help="Snapshot ID")
	args = parser.parse_args()

	try:
		if args.command == "init_storage":
			init_storage()
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
