import json
import logging
import time
import openai
import ollama
from utils import load_config

# Load configuration
config = load_config()
MAX_RETRIES = config['retry_settings']['max_retries']
RETRY_DELAY = config['retry_settings']['retry_delay']

def test_model(model_name, model_type='local', data_type='both', example_type='both'):
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
    real_data = load_data(config['paths']['data_directory'] + 'simple_examples.json', 
                          config['paths']['data_directory'] + 'complex_examples.json', 
                          data_type='real', example_type=example_type)
    synthetic_data = load_data(config['paths']['data_directory'] + 'augmented_examples.json', 
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

    for example in data_to_test:
        prompt = example['input_text']
        expected_output = example['expected_dsl_output']
        response = None

        for attempt in range(MAX_RETRIES):
            try:
                response = run_model_inference(
                    model_name=model_name,
                    model_type=model_type,
                    prompt=prompt,
                    precision=model_parameters.get('precision', 'full'),
                    quantization=model_parameters.get('quantization', None),
                    parameters=model_parameters
                )
                log_result(prompt, expected_output, response, success=(response == expected_output))
                break
            except Exception as e:
                logging.warning(f"Attempt {attempt + 1} failed for model {model_name} on input '{prompt}': {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    log_result(prompt, expected_output, response, success=False)
                    logging.error(f"Maximum retries reached for model {model_name} on input '{prompt}'.")

def log_result(prompt, expected_output, response, success):
    """Logs the result of each inference attempt."""
    log_file = config['paths']['test_results_file']
    log_entry = {
        'prompt': prompt,
        'expected_output': expected_output,
        'model_output': response,
        'success': success
    }
    with open(log_file, 'a') as file:
        json.dump(log_entry, file)
        file.write('\n')
