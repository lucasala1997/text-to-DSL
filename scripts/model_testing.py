import json
import logging
import time
import requests
import os
import subprocess
import traceback
from datetime import datetime
from utils import load_config
from scripts.message_builder import build_message
from tqdm import tqdm
from time import perf_counter  # Import at the top of the file if not already


# Load configuration
config = load_config()

# Set up logging based on config.json
logging.basicConfig(
    filename=config['paths']['project_log_file'],
    level=getattr(logging, config['logging']['level'], logging.INFO),
    format=config['logging']['format']
)

MAX_RETRIES = config['retry_settings']['max_retries']
RETRY_DELAY = config['retry_settings']['retry_delay']

# Closed-source models and their APIs
closed_source_models = {
    "OpenAI GPT4o": {
        "api_url": "https://api.openai.com/v1/chat/completions",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_keys']['openai_key']}"
        },
        "model_name_api": "gpt-4o"
    },
    "OpenAI GPT4o mini": {
        "api_url": "https://api.openai.com/v1/chat/completions",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_keys']['openai_key']}"
        },
        "model_name_api": "gpt-4o-mini"
    },
    "Claude 3.5 sonnet": {
        "api_url": "https://api.anthropic.com/v1/complete-chat",
        "headers": {
            "x-api-key": f"{config['api_keys']['claude_key']}",
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        },
        "model_name_api": "claude-3-5-sonnet-20241022"
    }
}

def load_model_config(model_name):
    """
    Loads the configuration for a specified model from a configuration file.

    Args:
        model_name (str): The name of the model for which to load the configuration.

    Returns:
        dict: A dictionary containing the model's configuration parameters.
    """
    model_config_file = config['paths']['model_parameters_file']
    try:
        with open(model_config_file, 'r') as file:
            all_model_configs = json.load(file)
            model_config = all_model_configs.get(model_name, {})

            if not model_config:
                logging.warning(f"No specific configuration found for model {model_name}. Using default settings.")

            return model_config
    except FileNotFoundError:
        logging.error(f"Model configuration file {model_config_file} not found: {e}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        return {}
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON in model configuration file {model_config_file}: {e}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        return {}

def test_model(dataset_name, model_name, system_prompt_version=None, data_type='both', example_type='both'):
    """Tests the selected model with specific settings and logs the results.
    
    Args:
        model_name (str): The name of the model to be tested.
        model_type (str): The type of model deployment ('local' or 'remote').
        data_type (str): The type of data to use ('real', 'synthetic', or 'both').
        example_type (str): The type of examples to run ('simple', 'complex', or 'both').

    Raises:
        Exception: If a model fails after the maximum number of retries.
    """
    # Define the paths for real data files
    real_data_files = ['simple_examples.json', 'complex_examples.json']

    # Load real data from both files
    try:
        real_data = [
            json.load(open(config['paths']['data_directory']+ dataset_name + '/' + file, 'r'))
            for file in real_data_files
        ]
        real_data = [item for sublist in real_data for item in sublist]  # Flatten the list if needed
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        return False
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON: {e}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        return False

    # Load synthetic data
    try:
        with open(config['paths']['data_directory'] + dataset_name + '/' + 'augmented_examples.json', 'r') as augmented_file:
            synthetic_data = json.load(augmented_file)
    except FileNotFoundError as e:
        logging.warning(f"Synthetic data file not found: {e}. Continuing without synthetic data.")
        synthetic_data = []  # If file not found, set synthetic_data to an empty list and continue
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON in synthetic data file: {e}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        return False
    
    # Combine data based on user preference
    data_to_test = []
    if data_type == 'real' or data_type == 'both':
        data_to_test.extend(real_data)
    if data_type == 'synthetic' or data_type == 'both':
        data_to_test.extend(synthetic_data)

    # Load model configuration
    model_config = load_model_config(model_name)

    # Load the relevant system prompt based on the user's choice (or default to "1.0" if None)
    system_prompt_file = config['paths']['system_prompt_versions']
    system_prompt = ""
    try:
        with open(system_prompt_file, 'r') as file:
            system_prompts = json.load(file)

            if system_prompt_version:
                # Search for the specific system prompt version
                system_prompt = system_prompt_version.get('prompt', None)
                if not system_prompt:
                    logging.warning(f"System prompt version {system_prompt_version} not found. Defaulting to version 1.0.")
            if not system_prompt:  # Load default if version is None or not found
                system_prompt = next((sp['prompt'] for sp in system_prompts if sp['version'] == "1.0"), "")
                if not system_prompt:
                    logging.error(f"Default system prompt (version 1.0) not found.")
                    return False  # Return False if no default prompt found
    except FileNotFoundError as e:
            logging.error(f"System prompt file {system_prompt_file} not found: {e}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            return False
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON in system prompt file {system_prompt_file}: {e}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        return False
    logging.info(f"Using system prompt: {system_prompt}")

    # Load the grammar file
    grammar_file = f"data/{dataset_name}/grammar.txt"
    grammar = ""
    try:
        with open(grammar_file, 'r') as file:
            grammar = file.read()
            logging.info(f"Grammar for {dataset_name} loaded successfully.")
    except FileNotFoundError as e:
        logging.error(f"Grammar file {grammar_file} not found: {e}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        return False
    
    # Load few-shot examples
    few_shot_examples_file = f"data/{dataset_name}/few_shot_examples.json"
    few_shot_examples = []
    try:
        with open(few_shot_examples_file, 'r') as file:
            few_shot_examples = json.load(file)
            logging.info(f"Few-shot examples for {dataset_name} loaded successfully.")
    except FileNotFoundError as e:
        logging.warning(f"Few-shot examples file {few_shot_examples_file} not found: {e}. Continuing without few-shot examples.")
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON in few-shot examples file {few_shot_examples_file}: {e}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        return False
    

    if model_config.get("type") == "closed source":
        # Closed-source model handling
        if model_name not in closed_source_models:
            logging.error(f"No configuration found for closed-source model: {model_name}")
            return False

        api_url = closed_source_models[model_name]['api_url']
        headers = closed_source_models[model_name]['headers']

        with tqdm(total=len(data_to_test), desc="Processing examples", unit="example") as pbar:

            for example in data_to_test:      
                start_time = perf_counter()  # Start the timer
        
                nl_dsl = example['input_text']
                expected_output = example['expected_dsl_output']
                complexity_level = example['complexity_level']

                # TODO: check system prompt
                # TODO: reimplement the message
                message = build_message(model_name, system_prompt, grammar, few_shot_examples, nl_dsl)
                print(message)
                if model_name == "Claude 3.5 sonnet":
                # Claude expects a 'prompt' field
                    data = {
                        "model": closed_source_models[model_name]['model_name_api'],
                        "prompt": message,  # Claude expects a single 'prompt' field
                        "max_tokens_to_sample": 5000  # Set this value based on your needs
                    }
                else:
                    # For other models like GPT-4o
                    data = {
                        "model": closed_source_models[model_name]['model_name_api'],
                        "messages": message
                    }

                # Retry logic for API requests
                for attempt in range(MAX_RETRIES):
                    try:
                        response = requests.post(api_url, headers=headers, json=data)
                        response_json = response.json()

                        if 'choices' in response_json:
                            response_content = response_json["choices"][0]["message"]["content"]
                        
                        #TODO: questo pezzo non credo serva più
                        try:
                            response_json = response.json()
                            logging.info(f"Full API response: {response_json}")
                            
                            if 'choices' in response_json and len(response_json['choices']) > 0:
                                response_content = response_json["choices"][0]["message"]["content"]
                                generated_dsl_output = response_content.strip()
                                logging.info(f"Generated DSL output: {generated_dsl_output}")
                            else:
                                logging.error("API response did not return expected 'choices' structure.")
                                generated_dsl_output = None
                        except Exception as e:
                            logging.error(f"Error processing API response: {e}")
                            generated_dsl_output = None


                        if response.status_code == 200:
                            generated_dsl_output = response_content
                            
                            # Calculate elapsed time
                            end_time = perf_counter()
                            time_taken = end_time - start_time  # Calculate time taken in seconds
                            
                            log_result(time_taken, nl_dsl, expected_output, generated_dsl_output, example['example_id'], model_name, system_prompt_version, complexity_level, parameters="unknown", time_taken=time_taken)
                            break
                        else:
                            logging.error(f"Error: {response.status_code} - {response.text}")
                            raise Exception(f"API request failed with status code {response.status_code}")
                    except Exception as e:
                        logging.warning(f"Attempt {attempt + 1} failed for model {model_name}: {e}")
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(RETRY_DELAY)
                        else:
                            log_result(nl_dsl, expected_output, None, example['example_id'], model_name, system_prompt_version, complexity_level, parameters=None, time_taken=None)
                            logging.error(f"Maximum retries reached for model {model_name}.")
                
                pbar.update(1)
            return True

    else:
        # Open-source model handling (e.g., via Ollama)
        base_url = "http://localhost:11434/v1/chat/completions"
        headers = {
            'Authorization': 'Bearer ollama',
            'Content-Type': 'application/json'
        }

        ollama_model = model_config.get("ollama_command", "")
        if not ollama_model:
            logging.error(f"Ollama command for model {model_name} not found.")
            return False

        # Load model parameters from the JSON configuration file
        model_config = load_model_config(model_name)
        parameters = model_config.get('parameters', {})
        logging.info(f"Testing model {model_name} with {len(data_to_test)} examples and parameters: {parameters}.")

        with tqdm(total=len(data_to_test), desc="Processing examples", unit="example") as pbar:

            for example in data_to_test:      
                start_time = perf_counter()  # Start the timer
      
                nl_dsl = example['input_text']
                expected_output = example['expected_dsl_output']
                complexity_level = example['complexity_level']

                response = None
                
                #Build the input message
                message = build_message(model_name, system_prompt, grammar, few_shot_examples, nl_dsl)
                
                data = {
                    "model": ollama_model,
                    "messages": message,
                    #"max_tokens": parameters.get('max_tokens', 2048),
                    "temperature": parameters.get('temperature'),
                    "seed": parameters.get('seed'), # Set at 7. Sets the random number seed to use for generation. Setting this to a specific number will make the model generate the same text for the same prompt. (Default: 0)
                    "num_predict": parameters.get('num_predict'), #Default = -2. Maximum number of tokens to predict when generating text. (Default: 128, -1 = infinite generation, -2 = fill context)
                    "num_ctx": parameters.get('num_ctx'), #Default = 2048. Sets the size of the context window used to generate the next token.
                    "top_p": parameters.get('top_p'), #Default = 0.9 Check if it is needed. we need to restrict the selection to a subset of the most probable tokens?
                    "top_k": parameters.get('top_k'), #Default = 40. Check if it is needed. we need to restrict the selection to a subset of the most probable tokens?
                }

                # Retry logic for API requests
                for attempt in range(MAX_RETRIES):
                    try:
                        # Send the request to the API
                        response = requests.post(base_url, headers=headers, json=data)

                        # Check if the request was successful
                        if response.status_code == 200:
                            result = response.json()
                            generated_dsl_output = result['choices'][0]['message']['content'].strip()
                            
                            # Calculate elapsed time
                            end_time = perf_counter()
                            time_taken = end_time - start_time  # Calculate time taken in seconds

                            log_result(nl_dsl, expected_output, generated_dsl_output, example['example_id'], model_name, system_prompt_version, complexity_level, parameters=parameters ,time_taken=time_taken)
                            break  # Exit loop on success
                        elif response.status_code == 404:
                            logging.error(f"Model {ollama_model} not found. Attempting to pull the model automatically.")
                            
                            # Run the ollama pull command using subprocess to pull the model
                            try:
                                subprocess.run(["ollama", "pull", ollama_model], check=True)
                                logging.info(f"Model {ollama_model} successfully pulled.")
                            except subprocess.CalledProcessError as e:
                                logging.error(f"Failed to pull model {ollama_model}: {e}")
                                return False
                        else:
                            logging.info(f"Payload sent to API: {json.dumps(data, indent=4)}")
                            logging.error(f"Error: {response.status_code} - {response.text}")
                            raise Exception(f"API request failed with status code {response.status_code}")

                    except Exception as e:
                        logging.warning(f"Attempt {attempt + 1} failed for model {model_name} on input '{message}': {e}")
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(RETRY_DELAY)  # Retry after a delay
                        else:
                            # Log the result in case of failure
                            log_result(nl_dsl, expected_output, None, example['example_id'], model_name, system_prompt_version, complexity_level, parameters=parameters, time_taken=None)
                            logging.error(f"Maximum retries reached for model {model_name} on input '{message}'.")
                pbar.update(1)
            return True


def log_result(prompt, expected_output, generated_output, example_id, model_name, system_prompt_version, complexity_level, parameters, time_taken):
    """Logs the result of each inference attempt with detailed information and validates the generated DSL."""
    
    # Prepare the result entry
    log_entry = {
        'test_id': f"test_run_{int(time.time())}",
        'example_id': example_id,
        'model_name': model_name,
        'system_prompt_version': system_prompt_version,
        'input_text': prompt,
        'expected_dsl_output': expected_output,
        'generated_dsl_output': generated_output,
        'complexity_level': complexity_level,
        'parameters': parameters,
        'time_taken': time_taken, 
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    # Folder where model-specific results will be saved
    log_folder = 'logs/models_results'
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    # Save results to a file based on model name
    log_file = f"{log_folder}/{model_name.replace(' ', '_').replace('/', '_')}.json"

    # Load existing log data if the file exists
    if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
        with open(log_file, 'r') as file:
            try:
                log_data = json.load(file)
            except json.JSONDecodeError:
                log_data = []
    else:
        log_data = []

    # Append the new result entry to the log
    log_data.append(log_entry)

    # Write the updated log data to the file
    with open(log_file, 'w') as file:
        json.dump(log_data, file, indent=4)
