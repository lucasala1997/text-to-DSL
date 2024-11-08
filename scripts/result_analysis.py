import json
import os
import logging
import requests
import nltk  # For BLEU score calculation
from nltk.translate.bleu_score import sentence_bleu
from collections import defaultdict
from utils import load_config


config = load_config()
# Set up logging based on config.json
logging.basicConfig(
    filename=config['paths']['project_log_file'],
    level=getattr(logging, config['logging']['level'], logging.INFO),
    format=config['logging']['format']
)

validator_url = "http://localhost:3000/api/sensor/validate"


def dsl_validator(expected_dsl_output, generated_dsl_output):
    if not expected_dsl_output.startswith("CREATE PRODUCT "):
        expected_dsl_output = "CREATE PRODUCT test USING 4326; " + expected_dsl_output
    if not generated_dsl_output.startswith("CREATE PRODUCT "):
        generated_dsl_output = "CREATE PRODUCT test USING 4326; " + generated_dsl_output
    
    # Ensure both outputs end with a semicolon
    if not expected_dsl_output.endswith(";"):
        expected_dsl_output += ";"
    if not generated_dsl_output.endswith(";"):
        generated_dsl_output += ";"

    data = {
        "expected_dsl_output": expected_dsl_output,
        "generated_dsl_output": generated_dsl_output
    }
    try:
        response = requests.post(validator_url, json=data)
        response.raise_for_status()
        result = response.json()
        #TODO: chiedi di cambiare la post e ritornare l'errore se c'è
        if not result.get("is_valid"):
            return False, result.get("full_output")
        return result.get("is_valid"), result.get("full_output")  # Returning both is_valid and full output for logging if needed
    except requests.exceptions.RequestException as e:
        logging.error(f"Request to DSL validator failed: {e}")
        return None, {}
    
def analyze_results():
    """Analyzes the logged test results for each model and calculates evaluation metrics including timing metrics."""
    try:
        # Directory where individual model results are stored
        models_results_folder = 'logs/models_results'

        if not os.path.exists(models_results_folder):
            logging.error(f"Models result folder {models_results_folder} does not exist.")
            return

        # Loop through each file in the models_results folder
        for model_file in os.listdir(models_results_folder):
            model_file_path = os.path.join(models_results_folder, model_file)
            
            if model_file.endswith('.json'):
                print(f"Analyzing results for model: {model_file}")
                # Load the test results for this model
                with open(model_file_path, 'r') as file:
                    results = json.load(file)

                # Track metrics by model, parameters, and system prompt version
                metrics = defaultdict(lambda: {
                    "accurate_dsl": 0,
                    "total_examples": 0,
                    "total_bleu_score": 0,
                    "total_time": 0,
                    "complex_time": 0,
                    "simple_time": 0,
                    "complex_count": 0,
                    "simple_count": 0
                })

                # Overall counters for this model
                total_examples = len(results)
                total_correct = 0
                total_bleu_score = 0
                total_time = 0

                # Analyze each result for this model
                model_name = os.path.splitext(model_file)[0]
                for result in results:
                    parameters = json.dumps(result['parameters'])  # Use the parameters as part of the key
                    system_prompt_version = result['system_prompt_version']['version']
                    time_taken = result.get('time_taken') or 0

                    key = (model_name, parameters, system_prompt_version)

                    metrics[key]["total_examples"] += 1
                    metrics[key]["total_time"] += time_taken
                    total_time += time_taken

                    # Separate time calculation based on complexity
                    if result['complexity_level'] == 'complex':
                        metrics[key]["complex_time"] += time_taken
                        metrics[key]["complex_count"] += 1
                    elif result['complexity_level'] == 'simple':
                        metrics[key]["simple_time"] += time_taken
                        metrics[key]["simple_count"] += 1
                    
                    # Update or set the 'success' key based on validation result
                    result['success'] = dsl_validator(result['expected_dsl_output'], result['generated_dsl_output'])[0]
                    print("success: "+ str(result['success']))
                    if result['success']:
                        metrics[key]["accurate_dsl"] += 1
                        total_correct += 1

                    # Calculate BLEU score if possible
                    if result['expected_dsl_output'] and result['generated_dsl_output']:
                        bleu_score = sentence_bleu([result['expected_dsl_output'].split()], result['generated_dsl_output'].split())
                        result['bleu_score'] = bleu_score
                        metrics[key]["total_bleu_score"] += bleu_score
                        total_bleu_score += bleu_score
                    else:
                        result['bleu_score'] = 0

                # After processing all results, save the updated list back to the file
                with open(model_file_path, 'w') as file:
                    json.dump(results, file, indent=4)

                # Calculate overall metrics for this model
                overall_accuracy = total_correct / total_examples
                overall_average_bleu_score = total_bleu_score / total_examples
                overall_average_time = total_time / total_examples if total_examples > 0 else 0

                # Add detailed metrics for each combination of parameters and system_prompt_version
                model_data = []
                for key, value in metrics.items():
                    model_name, parameters, system_prompt_version = key
                    # Calculate average times for each complexity level
                    avg_complex_time = value["complex_time"] / value["complex_count"] if value["complex_count"] > 0 else 0
                    avg_simple_time = value["simple_time"] / value["simple_count"] if value["simple_count"] > 0 else 0

                    # Ensure dictionary format for detailed metrics
                    detailed_entry = {
                        'parameters': json.loads(parameters),
                        'system_prompt_version': system_prompt_version,
                        'overall_accuracy': value['accurate_dsl'] / value['total_examples'],
                        'average_bleu_score': value['total_bleu_score'] / value['total_examples'],
                        'average_time': value["total_time"] / value["total_examples"] if value["total_examples"] > 0 else 0,
                        'average_complex_time': avg_complex_time,
                        'average_simple_time': avg_simple_time,
                        'total_examples': value['total_examples'],
                        'system_prompt_version': system_prompt_version
                    }
                    model_data.append(detailed_entry)

                # Save overall metrics for this model in a separate JSON file

                # If the overall folder doesn't exist in the model_results folder, create it
                overall_results_folder = os.path.join(models_results_folder, 'overall_results')
                if not os.path.exists(overall_results_folder):
                    os.makedirs(overall_results_folder)
                overall_metrics_file = os.path.join(overall_results_folder, f"overall_metrics_{model_name}.json")
                with open(overall_metrics_file, 'w') as metrics_file:
                    json.dump(model_data, metrics_file, indent=4)

                logging.info(f"Metrics analysis completed for model: {model_name}")

    except FileNotFoundError as fnf_error:
        logging.error(f"Error loading test results file: {fnf_error}")
    except json.JSONDecodeError as json_error:
        logging.error(f"Error parsing test results JSON: {json_error}")
