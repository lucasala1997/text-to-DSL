import requests
import json
import logging
import time
import os
from datetime import datetime
from time import perf_counter
from tqdm import tqdm
from utils import load_config
from scripts.result_analysis import analyze_results

model_name = "qwen2.5-coder:7b-base-fp16"

config = load_config()
# Set up logging based on config.json
logging.basicConfig(
    filename=config['paths']['project_log_file'],
    level=getattr(logging, config['logging']['level'], logging.INFO),
    format=config['logging']['format']
)

# Load few-shot examples
few_shot_examples_file = f"data/sensors/few_shot_examples.json"
few_shot_examples = []
with open(few_shot_examples_file, 'r') as file:
    few_shot_examples = json.load(file)
    
system_prompt = "You are a helpful assistant. You are tasked with generating Domain Specific Language (DSL) code for a given input. Respond only with the DSL code."
grammar_file = f"data/sensors/grammar.txt"
grammar = ""
with open(grammar_file, 'r') as file:
    grammar = file.read()
def log_result(prompt, expected_output, generated_output, example_id, model_name, system_prompt_version, complexity_level, parameters, time_taken):
    """Logs the result of each inference attempt with detailed information and validates the generated DSL."""
    try:
        # Prepare the result entry
        log_entry = {
            'test_id': f"test_run_{int(time.time())}",
            'example_id': "0",
            'model_name': model_name,
            'system_prompt_version': {
                'version': '1.0',
                'prompt': system_prompt,
                'rationale': 'Basic system prompt',
                'timestamp': '2024-10-10T10:00:00'
            },
            'input_text': prompt,
            'expected_dsl_output': expected_output,
            'generated_dsl_output': generated_output,
            'complexity_level': complexity_level,
            'parameters': parameters,
            'time_taken': time_taken, 
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

        # Folder where model-specific results will be saved
        log_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'models_results')
        os.makedirs(log_folder, exist_ok=True)
        logging.info(f"Saving results to folder: {log_folder}")

        # Save results to a file based on model name
        log_file = os.path.join(log_folder, f"{model_name.replace(' ', '_').replace('/', '_')}.json")
        logging.info(f"Saving to file: {log_file}")

        # Load existing log data if the file exists
        log_data = []
        if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
            try:
                with open(log_file, 'r') as file:
                    log_data = json.load(file)
                    if not isinstance(log_data, list):
                        log_data = []
                        logging.warning(f"Existing log file {log_file} did not contain a list, creating new list")
            except json.JSONDecodeError:
                logging.warning(f"Could not decode existing log file {log_file}, creating new list")
                log_data = []
        
        # Append the new result entry to the log
        log_data.append(log_entry)

        # Write the updated log data to the file
        with open(log_file, 'w') as file:
            json.dump(log_data, file, indent=4)
            logging.info(f"Successfully saved results for example {example_id}")

    except Exception as e:
        logging.error(f"Error in log_result: {str(e)}")
        raise


def build_message(system_prompt, grammar, few_shot_examples, nl_dsl):

  message = []
  # Combine system prompt and grammar in the system message
  if system_prompt or grammar:
      system_content = f"{system_prompt}\n\nRules that need to be followed to write the code:\n{grammar}"
      message.append({"role": "system", "content": system_content})
      print("The model has prompt and grammar")
  else:
      message.append({"role": "system", "content": system_prompt})

  # Add few-shot examples with alternating roles
  if few_shot_examples:
      for example in few_shot_examples:
          message.append({"role": "user", "content": example['input_text']})
          message.append({"role": "assistant", "content": example['expected_dsl_output']})

  # Final user input
  message.append({"role": "user", "content": nl_dsl})
  return message  # Add this line


real_data_files = ['simple_examples.json', 'complex_examples.json']
# Load real data from both files
real_data = [
    json.load(open(config['paths']['data_directory']+ "sensors" + '/' + file, 'r'))
    for file in real_data_files
]
real_data = [item for sublist in real_data for item in sublist]  # Flatten the list if needed


# Combine data based on user preference
data_to_test = []
data_to_test.extend(real_data)

# Open-source model handling (e.g., via Ollama)
base_url = "http://localhost:11434/v1/chat/completions"
headers = {
    'Authorization': 'Bearer ollama',
    'Content-Type': 'application/json'
}

with tqdm(total=len(data_to_test), desc="Processing examples", unit="example") as pbar:
    for example in data_to_test:      
        try:
            start_time = perf_counter()  # Start the timer

            nl_dsl = example['input_text']
            expected_output = example['expected_dsl_output']
            complexity_level = example['complexity_level']

            message = build_message(system_prompt, grammar, few_shot_examples, nl_dsl)
            logging.info(f"Processing example with input: {nl_dsl[:100]}...")  # Log truncated input

            data = {
                "model": model_name,
                "messages": message,
                "temperature": 0.1,
                "seed": 7,
                "num_predict": 10,
                "num_ctx": 8192,
                "top_p": 0.9,
                "top_k": 50,
            }
            
            # Send the request to the API
            logging.info("Sending request to Ollama API...")
            response = requests.post(base_url, headers=headers, json=data)
            logging.info(f"Received response with status code: {response.status_code}")

            # Check if the request was successful
            if response.status_code == 200:
                result = response.json()
                generated_dsl_output = result['choices'][0]['message']['content'].strip()
                logging.info(f"Generated output: {generated_dsl_output[:100]}...")  # Log truncated output
                
                # Calculate elapsed time
                end_time = perf_counter()
                time_taken = end_time - start_time

                # Prepare parameters for logging
                parameters = {
                    "temperature": 0.1,
                    "seed": 7,
                    "num_predict": -1,
                    "num_ctx": 8192,
                    "top_p": 0.9,
                    "top_k": 50
                }
                example_id = example.get('id', f'example_{time.time()}')
                system_prompt_version = "v1"

                # Log the result
                logging.info(f"Logging result for example {example_id}")
                log_result(
                    prompt=nl_dsl,
                    expected_output=expected_output,
                    generated_output=generated_dsl_output,
                    example_id=example_id,
                    model_name=model_name,
                    system_prompt_version=system_prompt_version,
                    complexity_level=complexity_level,
                    parameters=parameters,
                    time_taken=time_taken
                )
            else:
                logging.error(f"Request failed with status code: {response.status_code}")
                logging.error(f"Response content: {response.text}")
        except Exception as e:
            logging.error(f"Error processing example: {str(e)}")
        finally:
            pbar.update(1)


analyze_results()

