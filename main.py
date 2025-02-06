import logging
import argparse
import traceback  # Module to log exceptions
import itertools
import json
from tqdm import tqdm
from utils import load_config
from scripts.data_validation import validate_data
from scripts.model_parameter_config import configure_model_parameters
from scripts.prompt_version import configure_prompt_version
from scripts.model_testing import test_model
from scripts.result_analysis import analyze_results
from scripts.visualization_reporting import generate_visualizations
from scripts.automatic_model_parameter_config import automatic_configure_model_parameters
from scripts.generate_best_results import generate_best_results_table

# =============================================================================
# Load configuration and set up logging
# =============================================================================

try:
    config = load_config()
except Exception as e:
    logging.error(f"Error loading config in {__name__}: {e}")
    logging.error(f"Traceback: {traceback.format_exc()}")
    print(f"An unexpected error occurred while loading config: {e}")

try:
    # Remove any previously defined handlers to avoid duplicate logs
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    logging.basicConfig(
        filename=config['paths']['project_log_file'],
        level=config['logging']['level'],
        format=config['logging']['format']
    )
except Exception as e:
    print(f"Error setting up logging: {e}")
    print(f"Traceback: {traceback.format_exc()}")

# =============================================================================
# New Function: Select Model and Parameter Option
# =============================================================================

def select_model_and_parameters():
    """
    Presents a list of available LLMs from the model parameters file and prompts the user
    to select one, then asks which parameter type to test.
    
    Returns:
        tuple: (selected_model_info, parameter_option)
    """
    try:
        config_file = config['paths']['model_parameters_file']
        with open(config_file, 'r') as file:
            model_configs = json.load(file)
        models = list(model_configs.keys())
        print("Available Models:")
        for i, key in enumerate(models):
            model_info = model_configs[key]
            print(f"{i}: {model_info.get('model_name', key)}")
        selected_index = input("Select the model to test (enter the number): ")
        try:
            selected_index = int(selected_index)
            if selected_index < 0 or selected_index >= len(models):
                print("Invalid model selection. Exiting.")
                exit(1)
        except ValueError:
            print("Invalid input. Exiting.")
            exit(1)
        selected_model_key = models[selected_index]
        selected_model_info = model_configs[selected_model_key]
        
        print("\nSelect parameter type to test:")
        print("1: Best ones (from overall_best_parameters_set.json)")
        print("2: Test all combinations (from parameters_to_test.json)")
        param_option = input("Enter your choice (1/2): ")
        try:
            param_option = int(param_option)
            if param_option not in [1, 2]:
                print("Invalid parameter option. Exiting.")
                exit(1)
        except ValueError:
            print("Invalid input for parameter option. Exiting.")
            exit(1)
        return selected_model_info, param_option
    except Exception as e:
        logging.error(f"Error in select_model_and_parameters: {e}")
        print(f"Error in select_model_and_parameters: {e}")
        exit(1)

# =============================================================================
# Modified deploy_selected_model Function
# =============================================================================

def deploy_selected_model(dataset_name, prompt_version, selected_model_info=None, parameter_option=None):
    """
    Handles the deployment of the selected model using the specified parameters.
    
    If selected_model_info and parameter_option are provided, the function uses them to decide 
    which parameter grid to use:
      - Option 1: Uses the parameters from overall_best_parameters_set.json.
      - Option 2: Uses the parameters from parameters_to_test.json.
      
    In both cases, the code extracts unique values for each parameter and uses itertools.product
    to generate all possible combinations.
    
    If these arguments are not provided, the function falls back to manual configuration.
    """
    try:
        if not selected_model_info or not parameter_option:
            # Fallback to manual configuration
            selected_model = configure_model_parameters()
            if selected_model:
                selected_model_name = selected_model.get('model_name')
                print(f"\nDeploying and prompting the model: {selected_model_name}")
                if test_model(dataset_name, selected_model_name, prompt_version):
                    logging.info(f"Model {selected_model_name} tested successfully.")
                    print(f"Model {selected_model_name} tested successfully.")
                else:
                    logging.error(f"Model {selected_model_name} failed testing.")
                    print(f"Model {selected_model_name} failed testing.")
            return
        else:
            selected_model_name = selected_model_info.get("model_name")
            # Decide which file to use based on the parameter option.
            if parameter_option == 1:
                params_file = config['paths']['overall_best_parameters_set']
            elif parameter_option == 2:
                params_file = config['paths']['parameters_to_test']
            else:
                print("Invalid parameter option.")
                return

            with open(params_file, 'r') as file:
                params_data = json.load(file)
            parameter_grid = params_data.get('parameter_grid', [])
            if not parameter_grid:
                print(f"No parameters found in {params_file}.")
                return

            # Extract unique values for each parameter:
            temperature_values = set(param['temperature'] for param in parameter_grid if 'temperature' in param)
            top_p_values = set(param['top_p'] for param in parameter_grid if 'top_p' in param)
            top_k_values = set(param['top_k'] for param in parameter_grid if 'top_k' in param)

            # Create all combinations:
            combined_parameter_grid = [
                {'temperature': temp, 'top_p': top_p, 'top_k': top_k}
                for temp, top_p, top_k in itertools.product(temperature_values, top_p_values, top_k_values)
            ]

            # For each parameter set in the combined grid, configure and test the model:
            for params in tqdm(combined_parameter_grid, desc="Testing parameter combinations"):
                updated_model_config = automatic_configure_model_parameters(selected_model_name, new_parameters=params)
                if updated_model_config:
                    # Extract the model name from the updated configuration dictionary
                    updated_model_name = updated_model_config.get('model_name')
                    print(f"\nDeploying and prompting the model: {updated_model_name} with parameters: {params}")
                    if test_model(dataset_name, updated_model_name, prompt_version):
                        logging.info(f"Model {updated_model_name} tested successfully with parameters {params}.")
                        print(f"Model {updated_model_name} tested successfully with parameters {params}.")
                    else:
                        logging.error(f"Model {updated_model_name} failed testing with parameters {params}.")
                        print(f"Model {updated_model_name} failed testing with parameters {params}.")
                else:
                    logging.error("Failed to configure the model with parameters: " + str(params))
                    print(f"Failed to configure the model with parameters: {params}")
    except Exception as e:
        logging.error(f"Unexpected error in deploy_selected_model: {e}")
        logging.error(traceback.format_exc())
        print(f"An unexpected error occurred in deploy_selected_model: {e}")

# =============================================================================
# Pipeline Function
# =============================================================================

def run_pipeline(selected_steps):
    """Runs the specified steps in the Text-to-DSL project workflow."""
    dataset_name = "sensors"
    try:
        # (Optional) Data validation can be activated here.
        if 'data_validation' in selected_steps:
            print('Starting data validation...')
            logging.info('Starting data validation...')
            dataset_name = validate_data()
            print('Data validated successfully.')
            print('--------------------------')

        # Obtain the first system prompt as a dictionary.
        prompt_version = configure_prompt_version(1)
        # Alternatively, you could hard-code it:
        # prompt_version = {"prompt": "This is the first system prompt."}

        if 'automatic_test_model' in selected_steps:
            logging.info('Deploying models with automatic parameters test...')
            # The interactive selection happens here.
            selected_model_info, param_option = select_model_and_parameters()
            deploy_selected_model(dataset_name, prompt_version, selected_model_info, param_option)
            print('--------------------------')

        if 'analyze_results' in selected_steps:
            print('Analyzing results...')
            logging.info('Analyzing results...')
            analyze_results()
            print('Analysis saved.')
            print('--------------------------')

        if 'generate_visualizations' in selected_steps:
            print('Generating plots...')
            logging.info('Generating visualizations...')
            generate_visualizations()
            print('Plot saved.')
            print('--------------------------')

        if 'generate_best_results' in selected_steps:
            print('Generating best results table...')
            logging.info('Generating best results table...')
            generate_best_results_table()
            print('Best results table generated.')
            print('--------------------------')

        logging.info('Process completed successfully.')
        print('Process completed successfully.')

    except Exception as e:
        logging.error(f"Unexpected error in run_pipeline: {e}")
        logging.error(traceback.format_exc())
        print(f"An unexpected error occurred in run_pipeline: {e}")

# =============================================================================
# Main Function
# =============================================================================

def main():
    try:
        """Main function to orchestrate the Text-to-DSL project workflow using command-line arguments."""
        parser = argparse.ArgumentParser(description='Text-to-DSL Project Workflow')
        parser.add_argument(
            '--run',
            type=str,
            nargs='+',
            default=[
                'configure_prompt_version', 'automatic_test_model', 'analyze_results', 'manage_experiment_logs',
                'generate_visualizations', "generate_best_results"
            ],
            help="""Specify which steps to run in the pipeline. Options include:
        data_validation             : Validates data before using it.
        automatic_test_model      : Deploys a specified model locally or on a server and tests different parameter configurations.
        test_model                  : Deploys a specified model locally or on a server.
        configure_prompt_version  : Tracks and updates the versions of prompts used for testing.
        analyze_results             : Analyzes model test results.
        manage_experiment_logs      : Manages the logs of your experiments.
        generate_visualizations     : Creates visual reports of model performance.
        generate_best_results       : Generates a table with the best results.
        
        You can specify multiple steps, e.g., "--run data_validation test_model analyze_results".
        If no steps are provided, the entire pipeline is executed by default."""
        )

        args = parser.parse_args()

        # Let the user choose the mode before running the pipeline:
        print("Please choose an option:")
        print("1: Evaluate obtained results only")
        print("2: Test an LLM (run full pipeline)")
        user_choice = input("Enter your choice (1/2): ").strip()
        if user_choice == "1":
            # Run only the evaluation steps
            selected_steps = ["analyze_results", "generate_visualizations", "generate_best_results"]
        elif user_choice == "2":
            # Use the steps provided in the command-line arguments (default includes testing and evaluation)
            selected_steps = args.run
        else:
            print("Invalid choice. Exiting.")
            exit(1)

        logging.info(f'Starting the pipeline with the following steps: {selected_steps}')
        run_pipeline(selected_steps)

    except Exception as e:
        logging.error(f"Unexpected error in main: {e}")
        print(f"An unexpected error occurred in main: {e}")

if __name__ == "__main__":
    main()
