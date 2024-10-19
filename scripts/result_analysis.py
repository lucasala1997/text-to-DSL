import json
import os
import logging
import nltk  # For BLEU score calculation
from nltk.translate.bleu_score import sentence_bleu
from collections import defaultdict

def analyze_results():
    """Analyzes the logged test results and calculates evaluation metrics.

    This function calculates metrics like Exact Match Accuracy and BLEU score for each example
    and updates the test_results.json file to include these metrics.
    """
    try:
        test_results_file = 'logs/test_results.json'

        # Load the existing test results
        with open(test_results_file, 'r') as file:
            results = json.load(file)

        # Track metrics by model, parameters, and system prompt version
        metrics = defaultdict(lambda: {"exact_match_count": 0, "total_examples": 0, "total_bleu_score": 0})

        # Overall counters
        total_examples = len(results)
        total_exact_match = 0
        total_bleu_score = 0

        # Analyze each result
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

        # Calculate overall metrics
        overall_exact_match_accuracy = total_exact_match / total_examples
        overall_average_bleu_score = total_bleu_score / total_examples

        # Save the updated test results back to the file
        with open(test_results_file, 'w') as file:
            json.dump(results, file, indent=4)

        # Log overall results
        log_overall_metrics(overall_exact_match_accuracy, overall_average_bleu_score, metrics)

    except FileNotFoundError as fnf_error:
        logging.error(f"Error loading test results file: {fnf_error}")
    except json.JSONDecodeError as json_error:
        logging.error(f"Error parsing test results JSON: {json_error}")

def log_overall_metrics(overall_exact_match_accuracy, overall_average_bleu_score, metrics):
    """Logs overall metrics for the test results to a JSON file.
    
    Args:
        overall_exact_match_accuracy (float): The calculated exact match accuracy for all examples.
        overall_average_bleu_score (float): The average BLEU score for all examples.
        metrics (dict): The detailed metrics by model, parameters, and system prompt version.
    """
    overall_metrics = {
        'overall_exact_match_accuracy': overall_exact_match_accuracy,
        'overall_average_bleu_score': overall_average_bleu_score,
        'detailed_metrics': {}
    }

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

        # Add to detailed_metrics using model_name as the top key
        if model_name not in overall_metrics['detailed_metrics']:
            overall_metrics['detailed_metrics'][model_name] = []

        overall_metrics['detailed_metrics'][model_name].append(detailed_entry)

    # Write overall metrics to the file
    with open('logs/overall_metrics.json', 'w') as metrics_file:
        json.dump(overall_metrics, metrics_file, indent=4)
