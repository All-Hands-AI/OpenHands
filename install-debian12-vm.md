
https://jbt.github.io/markdown-editor/



# OpenDevin on Fresh Debian 12 VirtualMachine

The below instructions are specific to the version that matches these `lsb_release -a` details:

| - | - |
 --- | ---
| **Distributor ID** | Debian |
| **Description** | Debian GNU/Linux 12 (bookworm) |
| **Release** | 12 |
| **Codename** | bookworm |

## Installing Prerequisites
This distribution excludes _sudo_ by default so you must switch to root first.
```
su -
```
**IMPORTANT:** You will remain running as root until you `exit`

If this is a completely fresh install then you must update your repositories now.
```
apt update
apt upgrade
```

Next, install the _curl_ and _sudo_ packages as they will be used later.
```
apt install curl sudo
```


### Install Docker
The [OpenDevin project](https://github.com/OpenDevin/OpenDevin) requires Docker to be installed. Check [Docker's documentation](https://docs.docker.com/engine/install/debian/) for the most recent information if you have any problems with these steps.
```
apt install ca-certificates
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
```
Then add the repository to Apt's sources. This is a copy of the command from Docker's install guide.
```
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null
```
Finally, update the repositories and install Docker.
```
apt update
apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin 
```

Grant your normal user account permission to use the sudo command and manage Docker
```
usermod -aG sudo MYUSER
usermod -aG docker MYUSER
```

### Install Python
Python is already installed but not in a way that can be used with OpenDevin. You will need to install _python3-pip_ and _python3-venv_ then set up a virtual environment.

```
apt install python3-pip python3-venv
```

Return to your normal user account by exiting from root and then logout and back in again to update your sudo group membership.
```
exit
logout
```

Log back in to your box and continue as your regular account. **If this doesn't work, reboot the VM**. Check your group membership with `groups` to ensure docker is there, or try running `docker ps`

```
mkdir -p ~/python3/venv/OpenDevin
python3 -m venv ~/python3/venv/OpenDevin/
source ~/python3/venv/OpenDevin/bin/activate
```
Your command prompt will change and is now prefixed with the name of the virtual python environment. The directories you have created should be owned by your normal user. If you accidentally create the virtual environment in the wrong directory, you will have to delete it and create a new one in the correct location. This is because Python3 venvs have the path automatically hardcoded into the modules you install.

### Install NodeJS and npm
```
sudo apt install nodejs npm
```

### Cloning the repository
Git should already be installed
```
mkdir ~/source
cd ~/source
git clone https://github.com/OpenDevin/OpenDevin.git
```

### Setting up OpenDevin
Execute the following from from within the project's root folder (`/home/MYUSER/source/OpenDevin` if you've followed this guide). Installing the required packages will take several minutes, even on a fast connection. You will see the progress frequently update on-screen if the command is working.
```
python -m pip install -r requirements.txt
```

You must also create a directory to be used as the workspace. You may put an existing project here for OpenDevin to work with or leave it empty.
```
mkdir /home/MYUSER/source/MyWorkspace
```

The last part of setup is to build the front end of the project which must be done from within the `frontend` directory (`~/source/OpenDevin/frontend`)
```
cd ~/source/OpenDevin/frontend
npm build
```

## Running OpenDevin
Change directory to OpenDevin's root project directory and make sure `launchOpenDevin.sh` is executable (`chmod u+x launchOpenDevin.sh`).

Decide which LLM to use and obtain an API key for it. The project supports many so you can try different models as you please. For this example, we're using OpenAI so we're setting the environment variables to support that platform within the launch script. Here is the usage:

```
Usage: ./launchOpenDevin.sh --host [IP] --port [PORT] --model [LLM_MODEL] --workspace <WORKSPACE_PATH> --apikey <API_KEY>
```

Example:
```
MYUSER@mydebianvm:~/source/OpenDevin$ ./launchOpenDevin.sh --host 192.168.0.15 --model gpt-3.5-turbo-0125 --workspace ~/source/MyWorkspace/ --apikey KEYHERE
```



# Troubleshooting

 * Illegal instruction error after executing uvicorn.
   * This means your hardware is incompatible so you will need to use a different machine or adjust hardware settings if it is virtual. If you're trying to run this on very old hardware it is unlikely to ever work.
 * Python says its packages are managed externally. 
   * You have not activated your virtual environment. Remember to create the venv, make sure it is owned by the correct user, and then activate it.
