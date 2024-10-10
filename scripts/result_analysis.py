import json
import logging
import nltk  # For BLEU score calculation
from nltk.translate.bleu_score import sentence_bleu


#TODO: check and adjust to the ne files configuration
def analyze_results():
    """Analyzes the logged test results and calculates evaluation metrics.

    This function calculates metrics like Exact Match Accuracy and BLEU score for each example
    and logs them to a separate file for analysis.
    """
    try:
        with open('logs/test_results.json', 'r') as file:
            results = [json.loads(line) for line in file]

        exact_match_count = 0
        total_examples = len(results)
        total_bleu_score = 0

        for result in results:
            if result['success']:
                exact_match_count += 1
            bleu_score = sentence_bleu([result['expected_output'].split()], result['model_output'].split())
            total_bleu_score += bleu_score
            log_individual_metrics(result['prompt'], result['expected_output'], result['model_output'], bleu_score)

        exact_match_accuracy = exact_match_count / total_examples
        average_bleu_score = total_bleu_score / total_examples

        log_overall_metrics(exact_match_accuracy, average_bleu_score)

    except FileNotFoundError as fnf_error:
        logging.error(f"Error loading test results file: {fnf_error}")

def log_individual_metrics(prompt, expected_output, response, bleu_score):
    """Logs individual example metrics to a JSON file.
    
    Args:
        prompt (str): The input prompt used in the model.
        expected_output (str): The expected DSL output.
        response (str): The model-generated output.
        bleu_score (float): The calculated BLEU score for the example.
    """
    metrics_entry = {
        'prompt': prompt,
        'expected_output': expected_output,
        'model_output': response,
        'bleu_score': bleu_score
    }
    with open('logs/individual_metrics.json', 'a') as metrics_file:
        json.dump(metrics_entry, metrics_file)
        metrics_file.write('\n')

def log_overall_metrics(exact_match_accuracy, average_bleu_score):
    """Logs overall metrics for the test results to a JSON file.
    
    Args:
        exact_match_accuracy (float): The calculated exact match accuracy for all examples.
        average_bleu_score (float): The average BLEU score for all examples.
    """
    overall_metrics = {
        'exact_match_accuracy': exact_match_accuracy,
        'average_bleu_score': average_bleu_score
    }
    with open('logs/overall_metrics.json', 'w') as metrics_file:
        json.dump(overall_metrics, metrics_file, indent=4)
