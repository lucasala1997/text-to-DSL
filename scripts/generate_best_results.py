import json
import os
import logging
import csv
from utils import load_config

# Load configuration
try:
    config = load_config()
except Exception as e:
    logging.error(f"Error loading config in {__name__}: {e}")
    print(f"An unexpected error occurred while loading config: {e}")

# Set up logging based on config.json
try:
    logging.basicConfig(
        filename=config['paths']['project_log_file'],
        level=getattr(logging, config['logging']['level'].upper(), logging.INFO),
        format=config['logging']['format']
    )
except Exception as e:
    print(f"Error setting up logging: {e}")

def generate_best_results_table():
    """
    Reads the overall_results JSON files for each model and generates a CSV file
    with the best result per model, including the combination of parameters that gave that result.
    """
    try:
        # Directory where overall_results are stored
        overall_results_dir = os.path.join('logs', 'models_results', 'overall_results')

        # Output CSV file path
        output_csv = os.path.join('logs', 'best_model_results.csv')

        # Initialize a list to store best results per model
        best_results = []

        # Check if the directory exists
        if not os.path.isdir(overall_results_dir):
            logging.error(f"The directory {overall_results_dir} does not exist.")
            print(f"The directory {overall_results_dir} does not exist.")
            return

        # Iterate over each JSON file in the directory
        for filename in os.listdir(overall_results_dir):
            if filename.endswith('.json'):
                model_name = filename.replace('.json', '')
                file_path = os.path.join(overall_results_dir, filename)

                with open(file_path, 'r') as f:
                    data = json.load(f)

                # For each model, find the best result according to overall_accuracy and average_bleu_score
                best_result = None
                for entry in data:
                    if best_result is None:
                        best_result = entry
                    else:
                        # Compare overall_accuracy
                        if entry['overall_accuracy'] > best_result['overall_accuracy']:
                            best_result = entry
                        elif entry['overall_accuracy'] == best_result['overall_accuracy']:
                            # If overall_accuracy is the same, compare average_bleu_score
                            if entry['average_bleu_score'] > best_result['average_bleu_score']:
                                best_result = entry

                if best_result:
                    # Add model name to the best_result
                    best_result['model_name'] = model_name

                    # Append the best result to the list
                    best_results.append(best_result)
                else:
                    logging.warning(f"No valid results found in {filename}")
                    print(f"No valid results found in {filename}")
        
        # After collecting the best results, sort them
        best_results.sort(
            key=lambda x: (x['overall_accuracy'], x['average_bleu_score']),
            reverse=True
        )
        
        if not best_results:
            logging.warning("No best results to write to CSV.")
            print("No best results to write to CSV.")
            return

        # Now, write the best_results to a CSV file
        # Determine the fieldnames for CSV
        fieldnames = [
            'model_name',
            'parameters',
            'system_prompt_version',
            'overall_accuracy',
            'average_bleu_score',
            'average_time',
            'average_complex_time',
            'average_simple_time',
            'total_examples'
        ]

        with open(output_csv, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for result in best_results:
                # Flatten the parameters dictionary
                parameters = result.get('parameters', {})
                # Convert parameters dictionary to a string for CSV
                parameters_str = json.dumps(parameters)
                result['parameters'] = parameters_str

                # Ensure all required fields are present
                row = {field: result.get(field, '') for field in fieldnames}
                writer.writerow(row)

        logging.info(f"Best results per model have been saved to {output_csv}")
        print(f"Best results per model have been saved to {output_csv}")

    except Exception as e:
        logging.error(f"Error in generating best results table: {e}")
        print(f"Error in generating best results table: {e}")

if __name__ == '__main__':
    generate_best_results_table()
