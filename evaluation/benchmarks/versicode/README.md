# VersiCode benchmark

This project is used to evaluate the performance of the model on VersiCode. It includes:

- data: the test data needed and the model outputs
- inference_utils: inference scripts for ours tasks and models
- metric: scripts for calculating various metric
- output_processing: process the  the model output to facilitate the calculation of model metrics

# Details

1. **Prepare the environment**

   ```shell
   #create conda environment
   conda create -n VersiCode python==3.12
   
   #install requirements
   pip install -r requirements.txt
   ```

2. **Model inference**

   ```shell
   #cd inference_utils directory
   cd inference_utils
   #The script file starting with 'test' is used to test the local model
   #The script file at the beginning of the API is used to test the API call model
   #Modify the 30th line of code to specify the local model path
   #Modify the 10th and 12th lines of code to specify the base URL and model name
   python api_test_token_completion.py
   python test_token.py
   ...
   ```

3. **Process output**
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

4. **Metric**
   We have three metrics pass@k，em@k and cdc@k Due to our inability to automatically build a dynamic evaluation environment, we have not provided pass@k .

   ```shell
   #cd metric
   #Modify lines 137-140 in migration task (compute_migration_cdc_score.py) or 143-145 in block and line completion task (compute_versicode_cdc_score.py and compute_versicode_em_score.py) of the code to specify the data path and calculate the k-value of the metric
   python compute_migration_cdc_score.py
   python compute_versicode_cdc_score.py
   python compute_versicode_em_score.py
   
   #Modify line 9 in token_level_em_score.py to specify the data path
   python token_level_em_score.py
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

[Tongtong Wu](https://github.com/wutong8023), 
[Weigang Wu](https://github.com/Weigang-Wu), 
[Xingyu Wang](https://github.com/wxy879001), 
[Kang Xu](https://github.com/xk57238890),
[Suyu Ma](https://github.com/JOJO201)