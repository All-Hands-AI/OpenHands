# VersiCode benchmark

This project is used to evaluate the performance of the model on VersiCode. It includes:

- data: the test data needed and the model outputs
- inference_utils: inference scripts for ours tasks and models
- metric: scripts for calculating various metric
- output_processing: process the model output to facilitate the calculation of model metrics

# Details

1. **Prepare the environment**

   ```shell
   #create conda environment
   conda create -n VersiCode python==3.12

   #install requirements
   pip install -r requirements.txt
   ```

2. **Experiment Data**

    To obtain the experimental data, please visit the Hugging Face link: https://huggingface.co/datasets/AstoneNg/VersiCode.
    Locate the files `VersiCode_block_completion.json` and `VersiCode_migration.json` under the `experiment_data` directory, and place them in the `/data/test_data directory` of this project.


3. **Model inference**

   ```shell
   #cd inference_utils directory
   cd inference_utils

   #The script file starting with 'test' is used to test the local model
   #The script file at the beginning of the API is used to test the API call model

   #block level code completipn
   #Modify the 10th and 12th lines of code to specify the base URL and model name
   python api_test_block_completion.py
   #Modify the 30th line of code to specify the local model path
   python test_block.py

   # code migration (migration order is 'old_to_new')
   #Modify the 10th and 12th lines of code to specify the base URL and model name
   python api_code_migration.py
   #Modify the 30th line of code to specify the local model path
   python test_migration.py
   ```

4. **Process output**
   Process the output content of the model, remove redundant content, extract specified content for easy calculation of indicators.

   ```shell
   #cd output_processing
   cd output_processing

   #Extract content from<start> and <end>
   #Modify the 8th and 9th lines of code to specify the model and task granularity
   python clear_ans.py

   #In the block completion task and migration task, cdc@k The calculation of indicators needs to be targeted at key rows,
   #Modify lines 76 and 79 to specify the data path
   python choose_core_line_from_block_versicode.py
   python choose_core_line_from_migration_versicode.py
   ```

5. **Metric**
   We have three metrics pass@k，em@k and cdc@k Due to our inability to automatically build a dynamic evaluation environment, we have not provided pass@k .

   ```shell
   #cd metric
   cd metric

   #Modify lines 137-140 in migration task (compute_migration_cdc_score.py) or 143-145 in block and line completion task (compute_versicode_cdc_score.py and compute_versicode_em_score.py) of the code to specify the data path and calculate the k-value of the metric
   python compute_migration_cdc_score.py
   python compute_versicode_cdc_score.py
   python compute_versicode_em_score.py

   #Notes
   #We found limitations in the ISM@k and PM@k metrics for evaluating code generation, so they are used only as reference in our experiments.
   #Modify lines 261-265 in block and line completion task of the code to specify the data path and calculate the k-value of the metric
   python compute_ism_pm_score.py
   ```

# Citation

```
@article{versicode,
  author={Tongtong Wu and Weigang Wu and Xingyu Wang and Kang Xu and Suyu Ma and Bo Jiang and Ping Yang and Zhenchang Xing and Yuan-Fang Li and Gholamreza Haffari},
  title        = {VersiCode: Towards Version-controllable Code Generation},
  journal      = {CoRR},
  volume       = {abs/2406.07411},
  year         = {2024},
  url          = {https://arxiv.org/abs/2406.07411},
}
```

**Github url**: https://github.com/wutong8023/VersiCode

# Contributor

[Tongtong Wu](https://scholar.google.com/citations?hl=zh-CN&user=u1Qp8lUAAAAJ&view_op=list_works&sortby=pubdate), [Weigang Wu](https://scholar.google.com/citations?hl=zh-CN&user=UneIZo8AAAAJ), [Xingyu Wang](https://scholar.google.com/citations?hl=zh-CN&user=wqPJcxcAAAAJ), [Kang Xu](https://scholar.google.com/citations?hl=zh-CN&user=N1UUDi0AAAAJ), [Suyu Ma](https://scholar.google.com/citations?hl=zh-CN&user=NJHR1ukAAAAJ), [Bo Jiang](https://wutong8023.site/VersiCode/), [Ping Yang](https://scholar.google.com/citations?view_op=list_works&hl=en&hl=en&user=hrogvxoAAAAJ), [Zhenchang Xing](https://scholar.google.com/citations?hl=zh-CN&user=0vCxuH4AAAAJ), [Yuan-Fang Li](https://scholar.google.com/citations?hl=zh-CN&user=wufXO1kAAAAJ), [Gholamreza Haffari](https://scholar.google.com/citations?hl=zh-CN&user=Perjx5EAAAAJ)
