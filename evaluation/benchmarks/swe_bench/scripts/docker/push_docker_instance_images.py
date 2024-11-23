"""You should first perform the following steps:

1. Build the docker images. Install SWE-Bench first (https://github.com/princeton-nlp/SWE-bench). Then run:
```bash
export DATASET_NAME=princeton-nlp/SWE-bench_Lite
export SPLIT=test
export MAX_WORKERS=4
export RUN_ID=some-random-ID
python -m swebench.harness.run_evaluation \
    --dataset_name $DATASET_NAME \
    --split $SPLIT \
    --predictions_path gold \
    --max_workers $MAX_WORKERS \
    --run_id $RUN_ID \
    --cache_level instance
```

2. Then run this script to push the docker images to the docker hub. Some of the docker images might fail to build in the previous step - start an issue in the SWE-Bench repo for possible fixes.

To push the docker images for "princeton-nlp/SWE-bench_Lite" test set to the docker hub (e.g., under `docker.io/xingyaoww/`), run:
```bash
EVAL_DOCKER_IMAGE_PREFIX='docker.io/xingyaoww/' python3 evaluation/swe_bench/scripts/docker/push_docker_instance_images.py --dataset princeton-nlp/SWE-bench_Lite --split test
```
"""

import argparse

import docker
from datasets import load_dataset
from tqdm import tqdm

from openhands.core.logger import openhands_logger as logger

logger.setLevel('ERROR')
from evaluation.benchmarks.swe_bench.run_infer import get_instance_docker_image  # noqa

parser = argparse.ArgumentParser()
parser.add_argument('--dataset', type=str, default='princeton-nlp/SWE-bench_Lite')
parser.add_argument('--split', type=str, default='test')
args = parser.parse_args()

dataset = load_dataset(args.dataset, split=args.split)
client = docker.from_env()

pbar = tqdm(total=len(dataset))
counter = {'success': 0, 'failed': 0}

failed_instances = []
for instance in dataset:
    instance_id = instance['instance_id']
    image_name = f'sweb.eval.x86_64.{instance_id}'
    target_image_name = get_instance_docker_image(instance_id)

    print('-' * 100)
    # check if image exists
    try:
        image: docker.models.images.Image = client.images.get(image_name)
        image.tag(target_image_name)
        print(f'Image {image_name} -- tagging to --> {target_image_name}')
        ret_push = client.images.push(target_image_name)
        if isinstance(ret_push, str):
            print(ret_push)
        else:
            for line in ret_push:
                print(line)
        print(f'Image {image_name} -- pushed to --> {target_image_name}')
        counter['success'] += 1
    except docker.errors.ImageNotFound:
        print(f'ERROR: Image {image_name} does not exist')
        counter['failed'] += 1
        failed_instances.append(instance_id)
    finally:
        pbar.update(1)
        pbar.set_postfix(counter)

print(f'Success: {counter["success"]}, Failed: {counter["failed"]}')
print('Failed instances IDs:')
for failed_instance in failed_instances:
    print(failed_instance)
