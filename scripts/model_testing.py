import json
import logging
import time
import openai
#import ollama
import requests
import subprocess
import traceback
from datetime import datetime
from utils import load_config
from scripts.message_builder import build_message


# Load configuration
config = load_config()
MAX_RETRIES = config['retry_settings']['max_retries']
RETRY_DELAY = config['retry_settings']['retry_delay']

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
        
    #TODO: system_prompt should contain the user choice
    # system_prompt_file = config['paths']['system_prompt_versions']
    # try: 
    #     system_prompts = json.load(file)
    # except json.JSONDecodeError:
    #             logging.error(f"Error decoding JSON in system prompt file {system_prompt_file}.")
    #             system_prompt = ''

    # if system_prompt_version:
    #         try:
    #             with open(system_prompt_file, 'r') as file:
    #                 system_prompt = next((sp['system_prompt'] for sp in system_prompts if sp['version'] == system_prompt_version), '')
    #         except FileNotFoundError:
    #             logging.error(f"System prompt file {system_prompt_file} not found. Loadin")
    #             system_prompt = ''
    #         print(f"Using system prompt version: {system_prompt_version}")
    # else:
    #     # Load the first system prompt if no specific version is provided
    #     try:
    #         system_prompt = next((sp['system_prompt'] for sp in system_prompts if sp['version'] == "1.0"), '')
    #     except FileNotFoundError:
    #         logging.error(f"System prompt file {system_prompt_file} not found.")
    #         system_prompt = ''

    # Load the relevant system prompt based on the user's choice (or default to "1.0" if None)
    system_prompt_file = config['paths']['system_prompt_versions']
    system_prompt = ""

    try:
        with open(system_prompt_file, 'r') as file:
            system_prompts = json.load(file)

            if system_prompt_version:
                # Search for the specific system prompt version
                system_prompt = next((sp['prompt'] for sp in system_prompts if sp['version'] == system_prompt_version), "")
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
    print(f"Using system prompt: {system_prompt}")

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
        print(f"Error: Grammar file for {dataset_name} dataset not found.")
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
    

    # Load model parameters from the JSON configuration file
    model_config = load_model_config(model_name)
    parameters = model_config.get('parameters', {})

    logging.info(f"Testing model {model_name} with {len(data_to_test)} examples and parameters: {parameters}.")

    # Initialize base URL and headers for the LLM API request
    base_url = "http://localhost:11434/v1/chat/completions"  # Example URL for Ollama
    headers = {
        'Authorization': 'Bearer ollama',  # required, but unused
        'Content-Type': 'application/json'
    }

    # Retrieve the ollama_command from the model configuration
    ollama_model = model_config.get("ollama_command", "")
    if not ollama_model:
        logging.error(f"Ollama command for model {model_name} not found.")
        return False

    #TODO check the logic of the loop
    for example in data_to_test:     
        nl_dsl = example['input_text']
        expected_output = example['expected_dsl_output']
        response = None

        #Build the input message
        message = build_message(model_name, system_prompt, grammar, few_shot_examples, nl_dsl)
        # Prepare the data payload for the API request
        data = {
            "model": ollama_model,  # Model name like 'llama3.1:8b'
            "messages": [
                {"role": "system", "content": system_prompt},  # System prompt
                {"role": "user", "content": message}  # The message generated for the user
            ],
            #"max_tokens": parameters.get('max_tokens', 2048),
            "temperature": parameters.get('temperature'),
            #"top_p": parameters.get('top_p', 1.0), #TODO:Default = 1.0. Check if it is needed. we need to restrict the selection to a subset of the most probable tokens?
            #"frequency_penalty": parameters.get('frequency_penalty', 0), #Default = 0. We do not want to penalize the repetition of the same token
            #"presence_penalty": parameters.get('presence_penalty', 0) #Default = 0.  A positive value makes the model more likely to introduce novel tokens, encouraging the generation of new ideas or content. A value of 0 means no encouragement for novelty, allowing repetition or common tokens.
        }


        #TODO: gestisci il caso del modello non local
        #TODO: inserisci il system prompt
        for attempt in range(MAX_RETRIES):
            try:
                # Send the request to the API
                response = requests.post(base_url, headers=headers, json=data)

                # Check if the request was successful
                if response.status_code == 200:
                    result = response.json()
                    generated_dsl_output = result['choices'][0]['message']['content'].strip()
                    
                    print("______________________________________________________")
                    print(f"response: {result}")
                    print("______________________________________________________")
                    print(f"generated_dsl_output: {generated_dsl_output}")
                    print("______________________________________________________")

                    # Log the result
                    log_result(nl_dsl, expected_output, generated_dsl_output, example['example_id'], model_name, system_prompt_version, success=(generated_dsl_output == expected_output))
                    break  # Exit loop on success
                elif response.status_code == 404:
                    logging.error(f"Model {ollama_model} not found. Attempting to pull the model automatically.")
                    
                    # Run the `ollama pull` command using subprocess to pull the model
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
                    log_result(message, expected_output, None, example['example_id'], model_name, system_prompt_version, success=False)
                    logging.error(f"Maximum retries reached for model {model_name} on input '{message}'.")
        
    return True


def log_result(prompt, expected_output, response, example_id, model_name, system_prompt_version, success):
    """Logs the result of each inference attempt with detailed information."""
    log_file = config['paths']['test_results_file']
    log_entry = {
        'test_id': f"test_run_{int(time.time())}",
        'example_id': example_id,
        'model_name': model_name,
        'system_prompt_version': system_prompt_version,
        'input_text': prompt,
        'expected_dsl_output': expected_output,
        'generated_dsl_output': response,
        'success': success,  # Include success status
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    with open(log_file, 'a') as file:
        json.dump(log_entry, file, indent=4)  # Add indentation for better formatting
        file.write('\n')



