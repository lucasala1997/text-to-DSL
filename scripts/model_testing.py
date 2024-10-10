import json
import logging
import time
from openai import OpenAI
import ollama
from utils import load_config


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
        logging.error(f"Model configuration file {model_config_file} not found.")
        return {}
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON in model configuration file {model_config_file}.")
        return {}

def test_model(model_name, system_prompt_version=None, data_type='both', example_type='both'):
    """Tests the selected model with specific settings and logs the results.
    
    Args:
        model_name (str): The name of the model to be tested.
        model_type (str): The type of model deployment ('local' or 'remote').
        data_type (str): The type of data to use ('real', 'synthetic', or 'both').
        example_type (str): The type of examples to run ('simple', 'complex', or 'both').

    Raises:
        Exception: If a model fails after the maximum number of retries.
    """
    # Load validated data from JSON files
    
    real_data = config(config['paths']['data_directory'] + 'simple_examples.json', 
                          config['paths']['data_directory'] + 'complex_examples.json', 
                          data_type='real', example_type=example_type)
    synthetic_data = config(config['paths']['data_directory'] + 'augmented_examples.json', 
                               None, data_type='synthetic', example_type=example_type)

    # Combine data based on user preference
    data_to_test = []
    if data_type == 'real' or data_type == 'both':
        data_to_test.extend(real_data)
    if data_type == 'synthetic' or data_type == 'both':
        data_to_test.extend(synthetic_data)

    # Load model parameters from the JSON configuration file
    model_parameters = load_model_config(model_name)

    logging.info(f"Testing model {model_name} with {len(data_to_test)} examples and parameters: {model_parameters}.")

    client = OpenAI(
        base_url = 'http://localhost:11434/v1',
        api_key='ollama', # required, but unused
    )

    #TODO: system_prompt should contain the user choice
    system_prompt_file = config['paths']['system_prompt_versions']
    try: 

        system_prompts = json.load(file)
    except json.JSONDecodeError:
                logging.error(f"Error decoding JSON in system prompt file {system_prompt_file}.")
                system_prompt = ''

    if system_prompt_version:
            try:
                with open(system_prompt_file, 'r') as file:
                    system_prompt = next((sp['system_prompt'] for sp in system_prompts if sp['version'] == system_prompt_version), '')
            except FileNotFoundError:
                logging.error(f"System prompt file {system_prompt_file} not found. Loadin")
                system_prompt = ''
            print(f"Using system prompt version: {system_prompt_version}")
    else:
        # Load the first system prompt if no specific version is provided
        try:
            system_prompt = next((sp['system_prompt'] for sp in system_prompts if sp['version'] == "1.0"), '')
        except FileNotFoundError:
            logging.error(f"System prompt file {system_prompt_file} not found.")
            system_prompt = ''

    for example in data_to_test:
        
        prompt = example['input_text']
        expected_output = example['expected_dsl_output']
        response = None

        #TODO: find the model to implement
        #TODO: implement the function to load the right schema for each model
        #message = set_message(model_name, prompt)

        #TODO: gestisci il caso del modello non local
        #TODO: chose how to manage the documentation
        #TODO: concatenate to the prompt the documentation
        #TODO: use system_prompt

        for attempt in range(MAX_RETRIES):
            try:
                response = client.chat.completions.create(
                    model_name=message,
                    prompt=prompt,
                    #TODO: see how to pass the parameters
                    # parameters=model_parameters
                )
                log_result(prompt, expected_output, response, success=(response == expected_output),
                        example_id=example['example_id'], model_name=model_name,
                        system_prompt_version='prompt_1')
                break
            except Exception as e:
                logging.warning(f"Attempt {attempt + 1} failed for model {model_name} on input '{prompt}': {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    log_result(prompt, expected_output, response, success=False)
                    logging.error(f"Maximum retries reached for model {model_name} on input '{prompt}'.")

def log_result(prompt, expected_output, response, example_id, model_name, system_prompt_version):
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
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    }
    
    with open(log_file, 'a') as file:
        json.dump(log_entry, file)
        file.write('\n')

