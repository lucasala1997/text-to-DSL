import json
import os
import logging
import nltk  # For BLEU score calculation
from nltk.translate.bleu_score import sentence_bleu
from collections import defaultdict

def analyze_results():
    """Analyzes the logged test results for each model and calculates evaluation metrics.

    This function calculates metrics like Exact Match Accuracy and BLEU score for each example
    and saves the results into separate overall_metrics files per model.
    """
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
                # Load the test results for this model
                with open(model_file_path, 'r') as file:
                    results = json.load(file)

                # Track metrics by model, parameters, and system prompt version
                metrics = defaultdict(lambda: {"exact_match_count": 0, "total_examples": 0, "total_bleu_score": 0})

                # Overall counters for this model
                total_examples = len(results)
                total_exact_match = 0
                total_bleu_score = 0

                # Analyze each result for this model
                for result in results:
                    model_name = result['model_name']
                    parameters = json.dumps(result['parameters'])  # Use the parameters as part of the key
                    system_prompt_version = result['system_prompt_version']['version']

                    key = (model_name, parameters, system_prompt_version)

                    metrics[key]["total_examples"] += 1
                    if result['generated_dsl_output'] == result['expected_dsl_output']:
                        result['success'] = True
                        metrics[key]["exact_match_count"] += 1
                        total_exact_match += 1
                    else:
                        result['success'] = False

                    # Calculate BLEU score
                    bleu_score = sentence_bleu([result['expected_dsl_output'].split()], result['generated_dsl_output'].split())
                    result['bleu_score'] = bleu_score  # Add BLEU score directly to the test result
                    metrics[key]["total_bleu_score"] += bleu_score
                    total_bleu_score += bleu_score

                # Calculate overall metrics for this model
                overall_exact_match_accuracy = total_exact_match / total_examples
                overall_average_bleu_score = total_bleu_score / total_examples

                # Save the updated test results back to the individual model file
                with open(model_file_path, 'w') as file:
                    json.dump(results, file, indent=4)

                # Prepare the overall metrics for this model
                overall_metrics = {
                    'overall_exact_match_accuracy': overall_exact_match_accuracy,
                    'overall_average_bleu_score': overall_average_bleu_score,
                    'detailed_metrics': {}
                }

                # Add detailed metrics for each combination of parameters and system_prompt_version
                for key, value in metrics.items():
                    model_name, parameters, system_prompt_version = key

                    # Ensure dictionary format for detailed metrics
                    detailed_entry = {
                        'exact_match_accuracy': value['exact_match_count'] / value['total_examples'],
                        'average_bleu_score': value['total_bleu_score'] / value['total_examples'],
                        'total_examples': value['total_examples'],
                        'system_prompt_version': system_prompt_version,
                        'parameters': json.loads(parameters)  # Convert parameters string back to dictionary
                    }

                    overall_metrics['detailed_metrics'][f"{system_prompt_version}"] = detailed_entry

                # Save overall metrics for this model in a separate JSON file
                overall_metrics_file = f"logs/models_results/overall_metrics_{model_name.replace(' ', '_').replace('(', '').replace(')', '').replace(':', '').replace('-', '_')}.json"
                with open(overall_metrics_file, 'w') as metrics_file:
                    json.dump(overall_metrics, metrics_file, indent=4)

                logging.info(f"Metrics analysis completed for model: {model_name}")

    except FileNotFoundError as fnf_error:
        logging.error(f"Error loading test results file: {fnf_error}")
    except json.JSONDecodeError as json_error:
        logging.error(f"Error parsing test results JSON: {json_error}")

