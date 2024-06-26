# How to Create a Custom Docker Sandbox 

The default OpenDevin sandbox comes with a [minimal ubuntu configuration](https://github.com/OpenDevin/OpenDevin/blob/main/containers/sandbox/Dockerfile). Your use case may need additional software installed by default. This guide will teach you how to accomplish this by utilizing a custom docker image. 

## Setup

To get started running with your own Docker Sandbox image you need to ensure you can build OpenDevin locally via the following: 
1. Clone the OpenDevin github repository to your local machine 
2. In the root (OpenDevin/)  directory, run ```make build```
3. Then run ```make run```  
4. Finally navigate your browser to ```localhost:3001``` to ensure that your local build of OpenDevin is functional 

> Note that the above steps will take some time to run and will require that your have python3.11, poetry (a python package manager), and Docker installed 


## Create Your Docker Image

Next you must create your custom docker image, which should be debian/ubuntu based. For example if we want want OpenDevin to have access to the "node" binary, we would use the following Dockerfile:  
```bash
# Start with latest ubuntu image
FROM ubuntu:latest

# Run needed updates
RUN apt-get update && apt-get install

# Install node
RUN apt-get install -y nodejs
```
Next build your docker image with the name of your choice, for example "custom_image". To do this you can create a directory and put your file inside it with the name "Dockerfile", and inside the directory run the following command: 
```docker build -t custom_image .``` 

This will produce a new image called ```custom_image``` that will be available in Docker Engine. 

> Note that in the configuration described in this document, OpenDevin will run as user "opendevin" inside the sandbox and thus all packages installed via the docker file should be available to all users on the system, not just root
> 
> Installing with apt-get above installs node for all users 


## Specify your custom image in config.toml file

OpenDevin configuration occurs via the top level ```config.toml``` file. 
Create a ```config.toml``` file in the OpenDevin directory and enter these contents: 
```
[core]
workspace_base="./workspace"
persist_sandbox=false
run_as_devin=true
sandbox_container_image="custom_image"
```
> Ensure that sandbox_container_image is set to the name of your custom image from the previous step

## Run  
Run OpenDevin by running ```make run``` in the top level directory.  
A lot of things will happen but ultimately the OpenDevin server and frontend should be running.

Navigate to ```localhost:3001``` and check if your desired dependencies are available.  

In the case of the example above, running ```node -v``` in the terminal produces ```v18.19.1``` 

Congratulations! 

## Technical Explanation 

The relevant code is defined in [ssh_box.py](https://github.com/OpenDevin/OpenDevin/blob/main/opendevin/runtime/docker/ssh_box.py) and [image_agnostic_util.py](https://github.com/OpenDevin/OpenDevin/blob/main/opendevin/runtime/docker/image_agnostic_util.py). 

In particular, ssh_box.py checks the config object for ```config.sandbox_container_image``` and then attempts to retrieve the image using [get_od_sandbox_image](https://github.com/OpenDevin/OpenDevin/blob/main/opendevin/runtime/docker/image_agnostic_util.py#L72) which is defined in image_agnostic_util.py. 

When first using a custom image, it will not be found and thus it will be built (on subsequent runs the built image will be found and returned). 

The custom image is built using [_build_sandbox_image()](https://github.com/OpenDevin/OpenDevin/blob/main/opendevin/runtime/docker/image_agnostic_util.py#L29), which creates a docker file using your custom_image as a base and then configures the environment for OpenDevin, like this: 
```
dockerfile_content = (
        f'FROM {base_image}\n'
        'RUN apt update && apt install -y openssh-server wget sudo\n'
        'RUN mkdir -p -m0755 /var/run/sshd\n'
        'RUN mkdir -p /opendevin && mkdir -p /opendevin/logs && chmod 777 /opendevin/logs\n'
        'RUN wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"\n'
        'RUN bash Miniforge3-$(uname)-$(uname -m).sh -b -p /opendevin/miniforge3\n'
        'RUN bash -c ". /opendevin/miniforge3/etc/profile.d/conda.sh && conda config --set changeps1 False && conda config --append channels conda-forge"\n'
        'RUN echo "export PATH=/opendevin/miniforge3/bin:$PATH" >> ~/.bashrc\n'
        'RUN echo "export PATH=/opendevin/miniforge3/bin:$PATH" >> /opendevin/bash.bashrc\n'
    ).strip()
```

> Note: the name of the image is modified via [_get_new_image_name()](https://github.com/OpenDevin/OpenDevin/blob/main/opendevin/runtime/docker/image_agnostic_util.py#L63) and it is the modified name that is searched for on subsequent runs 




## Troubleshooting / Errors 

### Error: ```useradd: UID 1000 is not unique```
If you see this error in the console output it is because OpenDevin is trying to create the opendevin user in the sandbox with a UID of 1000, however this UID is already being used in the image (for some reason). To fix this change the sandbox_user_id field in the config.toml file to a different value: 
```
[core]
workspace_base="./workspace"
persist_sandbox=false
run_as_devin=true
sandbox_container_image="custom_image"
sandbox_user_id="1001"
```

### Port use errors 
If you see an error about a port being in use or unavailable, try deleting all running Docker Containers and then re-running ```make run``` 

## Discuss 

For other issues or questions join the [Slack](https://join.slack.com/t/opendevin/shared_invite/zt-2jsrl32uf-fTeeFjNyNYxqSZt5NPY3fA) or [Discord](https://discord.gg/ESHStjSjD4) and ask! 