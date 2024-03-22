import json
import argparse
from datasets import load_dataset
from transformers import LlamaForCausalLM, CodeLlamaTokenizer

def generate_code(dataset_path, model_path, output_file):
    dataset = load_dataset(dataset_path)
    tokenizer = CodeLlamaTokenizer.from_pretrained(model_path)
    model = LlamaForCausalLM.from_pretrained(model_path)

    results = []

    for prompt in dataset['dev']['text']:
        input_ids = tokenizer(prompt, return_tensors="pt")["input_ids"]
        generated_ids = model.generate(input_ids, max_new_tokens=4096)
        filling = tokenizer.batch_decode(generated_ids[:, input_ids.shape[1]:], skip_special_tokens=True)[0]
        completed_code = prompt.replace("<FILL_ME>", filling)
        results.append(completed_code)

    with open(output_file, 'w') as f:
        json.dump(results, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate code using a pre-trained model.")
    parser.add_argument("--dataset_path", type=str, required=True, help="Path to the dataset.")
    parser.add_argument("--model_path", type=str, required=True, help="Path to the pre-trained model.")
    parser.add_argument("--output_file", type=str, default="generated_code.json", help="Path to save the generated code.")

    args = parser.parse_args()

    generate_code(args.dataset_path, args.model_path, args.output_file)
