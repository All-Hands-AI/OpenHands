import argparse
import os
import subprocess
from datasets import load_dataset


# Function to run shell commands
def run_command(command):
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f'An error occurred: {e}')


# Function to log in to Docker Hub
def docker_login():
    print('Logging into Docker Hub...')
    run_command('docker login')


# Function to generate Dockerfile content based on image type
def generate_dockerfile_content(base_image, dependencies, datum, image_type, patch_path, test_patch_path, preds_path):
    dockerfile_content = f"""
FROM {base_image}
RUN pip install {' '.join(dependencies)}
COPY {patch_path} /app/patch.diff
RUN git apply /app/patch.diff
RUN rm /app/patch.diff
COPY {test_patch_path} /app/patch.diff
RUN git apply /app/patch.diff
RUN git config --global user.email ""
RUN git config --global user.name "TestGenEval"
RUN rm /app/patch.diff
RUN rm {datum['test_file']}
"""

    # Add specific content based on image type
    if image_type == 'full':
        dockerfile_content += "RUN git add .\nRUN git commit -m \"Testing fixes\""
    elif image_type in ['first', 'last', 'extra']:
        dockerfile_content += f"COPY {preds_path[image_type]} {datum['test_file']}\nRUN git add .\nRUN git commit -m \"Testing fixes\""

    return dockerfile_content


# Function to build, push, and clean up Docker images
def build_and_push_image(dockerfile_content, image_name):
    with open('Dockerfile.temp', 'w') as dockerfile:
        dockerfile.write(dockerfile_content)
    run_command(f'docker build -f Dockerfile.temp -t {image_name} .')
    run_command(f'docker push {image_name}')
    run_command(f'docker rmi {image_name}')
    os.remove('Dockerfile.temp')


# Function to process images with .eval in the name
def process_images(dataset, original_namespace, new_namespace):
    dependencies = ['coverage', 'cosmic-ray']

    for datum in dataset:
        full_image_name = f'{original_namespace}/sweb.eval.x86_64.{datum["instance_id"].replace("__", "_s_")}:latest'
        print(f'Processing image: {full_image_name}')
        run_command(f'docker pull {full_image_name}')

        # Save patches and preds_context to regular files
        patch_file_path = 'patch.diff'
        test_patch_file_path = 'test_patch.diff'
        preds_paths = {
            'first': 'preds_first.txt',
            'last': 'preds_last_minus_one.txt',
            'extra': 'preds_last.txt'
        }

        with open(patch_file_path, 'w') as patch_file, \
             open(test_patch_file_path, 'w') as test_patch_file, \
             open(preds_paths['first'], 'w') as first_file, \
             open(preds_paths['last'], 'w') as last_minus_one_file, \
             open(preds_paths['extra'], 'w') as last_file:

            patch_file.write(datum['patch'])
            test_patch_file.write(datum['test_patch'])
            first_file.write(datum['preds_context']['first'])
            last_minus_one_file.write(datum['preds_context']['last_minus_one'])
            last_file.write(datum['preds_context']['last'])

        # Define image types and corresponding tags
        image_types = ['full', 'first', 'last', 'extra']
        for image_type in image_types:
            new_image_name = f'{new_namespace}/sweb.eval.x86_64.{datum["instance_id"].replace("__", "_s_")}_{image_type}:latest'
            dockerfile_content = generate_dockerfile_content(full_image_name, dependencies, datum, image_type, patch_file_path, test_patch_file_path, preds_paths)
            build_and_push_image(dockerfile_content, new_image_name)

        # Cleanup regular files and images
        os.remove(patch_file_path)
        os.remove(test_patch_file_path)
        os.remove(preds_paths['first'])
        os.remove(preds_paths['last'])
        os.remove(preds_paths['extra'])
        run_command(f'docker rmi {full_image_name}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process Docker images with .eval in the name.')
    parser.add_argument('--dataset', type=str, default='kjain14/testgeneval')
    parser.add_argument('--split', type=str, default='test')
    parser.add_argument('--new_namespace', type=str, default='kdjain', help='The new Docker Hub namespace to push the images')
    parser.add_argument('--original_namespace', type=str, default='xingyaoww', help='The original Docker Hub namespace')

    args = parser.parse_args()
    dataset = load_dataset(args.dataset)[args.split]

    docker_login()
    process_images(dataset, args.original_namespace, args.new_namespace)
