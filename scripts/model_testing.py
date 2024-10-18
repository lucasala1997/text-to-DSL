import json
import logging
import time
import openai
#import ollama
import requests
import traceback
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

    # Load model parameters from the JSON configuration file
    model_config = load_model_config(model_name)
    parameters = model_config.get('parameters', {})

    logging.info(f"Testing model {model_name} with {len(data_to_test)} examples and parameters: {parameters}.")

    #TODO: change to requests
    # client = OpenAI(
    #     base_url = 'http://localhost:11434/v1',
    #     api_key='ollama', # required, but unused
    # )

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

    logging.info(f"Using grammar: {grammar}")

    
    # Load few-shot examples
    few_shot_examples_file = f"{dataset_name}/few_shot_examples.json"
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
    
    #TODO check the logic of the loop
    for example in data_to_test:
        
        
        example = example['input_text']
        # expected_output = example['expected_dsl_output']
        response = None

        message = build_message(model_name, system_prompt, grammar, few_shot_examples, example)

        #TODO: gestisci il caso del modello non local
        #TODO: inserisci il system prompt
        for attempt in range(MAX_RETRIES):
            try:
                response = client.chat.completions.create(
                    model_name=model_name,
                    prompt=message,
                    #TODO: see how to pass the parameters
                    parameters=parameters
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
    return True

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

