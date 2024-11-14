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
# import tensorflow as tf


#TODO: check if VRAM usage is working
# GPU Memory Management
# try:
#     # Option 1: TensorFlow VRAM limit (use if TensorFlow is in your project)
#     import tensorflow as tf

#     gpus = tf.config.experimental.list_physical_devices('GPU')
#     if gpus:
#         try:
#             for gpu in gpus:
#                 tf.config.experimental.set_memory_growth(gpu, True)  # Enable dynamic growth
#                 tf.config.experimental.set_virtual_device_configuration(
#                     gpu,
#                     [tf.config.experimental.VirtualDeviceConfiguration(
#                         memory_limit=int(0.4 * gpu.memory_info().total))]  # Set to 40% of total VRAM
#                 )
#         except RuntimeError as e:
#             print(f"Error setting TensorFlow VRAM limit: {e}")
# except ImportError:
#     pass  # TensorFlow not installed, skipping setup

# try:
#     # Option 2: PyTorch VRAM limit (use if PyTorch is in your project)
#     import torch
#     torch.cuda.set_per_process_memory_fraction(0.4)  # Set memory usage limit to 40%
# except ImportError:
#     pass  # PyTorch not installed, skipping setup

# Load configuration
try:
    config = load_config()
except Exception as e:
    logging.error(f"Error loading config in {__name__}: {e}")
    logging.error(f"Traceback: {traceback.format_exc()}")  # Log the detailed traceback
    (f"An unexpected error occurred while loading config: {e}")

# Setup logging based on config settings (config.json)
try:
    # Reset any existing handlers to avoid duplicate logs
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Configure logging with the settings from config.json
    logging.basicConfig(
        filename=config['paths']['project_log_file'],
        level=config['logging']['level'],
        format=config['logging']['format']
    )
except Exception as e:
    print(f"Error setting up logging: {e}")
    print(f"Traceback: {traceback.format_exc()}")

def deploy_selected_model(dataset_name, prompt_version=None, automatic=False):
    try:
        """Handles the deployment of the selected model using the latest parameters."""
        if automatic:
            
            config_file = config['paths']['model_parameters_file']
            # Load existing parameters from the JSON file
            with open(config_file, 'r') as file:
                model_configs = json.load(file)
            
             # Extract the list of model names
            model_names = [info["model_name"] for info in model_configs.values() if "model_name" in info]


            try:
                #parameters_to_test=config['paths']['parameter_to_test']
                parameters_to_test=config['paths']['dummy_parameter_to_test']
                with open(parameters_to_test, 'r') as file:
                    parameters = json.load(file)
                    parameter_grid = parameters['parameter_grid']
            except Exception as e:
                logging.error(f"Error loading parameter grid: {e}")
                return []
            
            # Extract unique values for each parameter
            temperature = set(param['temperature'] for param in parameter_grid if 'temperature' in param)
            top_p = set(param['top_p'] for param in parameter_grid if 'top_p' in param)
            top_k = set(param['top_k'] for param in parameter_grid if 'top_k' in param)

            
            parameter_grid = [
                {'temperature': temp, 'top_p': top_p, 'top_k': top_k}
                for temp, top_p, top_k in itertools.product(temperature, top_p, top_k)
            ]
            for params in tqdm(parameter_grid, desc="Testing parameter combinations"):
                # Pass the current parameter combination to automatic_configure_model_parameters
                #TODO: passagli anche il nome del modello altrimenti lo chiede ogni volta (da file)
                selected_model = automatic_configure_model_parameters(model_names[1], new_parameters=params)
                
                if selected_model:
                    print(f"\nDeploying and prompting the model: {selected_model}")
                    
                    # Test the model with the configured parameters
                    if test_model(dataset_name, selected_model, prompt_version):
                        logging.info(f"Model {selected_model} tested successfully.")
                        print(f"Model {selected_model} tested successfully.")
                    else:
                        logging.error(f"Model {selected_model} failed testing.")
                        print(f"Model {selected_model} failed testing.")
                else:
                    logging.error("Failed to configure the model with parameters:", params)
        else:
            selected_model = configure_model_parameters()

            if selected_model:
                selected_model_name = selected_model.get('model_name')  # Extract the model name
                print(f"\nDeploying and prompting the model: {selected_model_name}")
                if test_model(dataset_name, selected_model_name, prompt_version):
                    logging.info(f"Model {selected_model_name} tested successfully.")
                    print(f"Model {selected_model_name} tested successfully.")
                else:
                    logging.error(f"Model {selected_model_name} failed testing.")
                    print(f"Model {selected_model_name} failed testing.")
    except Exception as e:
        logging.error(f"Unexpected error in {__name__}.deploy_selected_model: {e}")
        logging.error(f"Traceback: {traceback.format_exc()}")  # Log the detailed traceback
        print(f"An unexpected error occurred in deploy_selected_model: {e}")

def run_pipeline(selected_steps):
    """Runs the specified steps in the Text-to-DSL project workflow."""

    dataset_name = "sensors"
    try:
        if 'data_validation' in selected_steps:
            print('Starting data validation...')
            logging.info('Starting data validation...')
            dataset_name = validate_data()
            print('Data validated successfully.')
            print('--------------------------')

        if 'configure_prompt_version' in selected_steps:
            print('Selecting prompt versions...')
            logging.info('Selecting prompt versions...')
            prompt_version = 1
            if 'automatic_test_model' not in selected_steps:
                prompt_version = configure_prompt_version()
            else:
                prompt_version = configure_prompt_version(prompt_version)
            print(f"Selected prompt version: {prompt_version}")
            print('--------------------------')

        if 'test_model' in selected_steps:
            print('Deploying models...')
            logging.info('Deploying models...')
            deploy_selected_model(dataset_name, prompt_version, automatic=False) if prompt_version else deploy_selected_model(dataset_name)
            print('--------------------------')
        
        if 'automatic_test_model' in selected_steps:
            logging.info('Deploying models with automatic parameters test...')
            deploy_selected_model(dataset_name, prompt_version, automatic=True) if prompt_version else deploy_selected_model(dataset_name, prompt_version=0, automatic=True)
            print('--------------------------')

        if 'analyze_results' in selected_steps:
            print('Analyzing results...')
            logging.info('Analyzing results...')
            analyze_results()
            print('Analysis saved.')
            print('--------------------------')

        if 'generate_visualizations' in selected_steps:
            print('Generating plots...')
            logging.info('Generating plots...')
            logging.info('Generating visualizations...')
            generate_visualizations()
            print('Plot saved.')
            print('--------------------------')

        logging.info('Process completed successfully.')
        print('Process completed successfully.')

    except Exception as e:
        logging.error(f"Unexpected error in {__name__}.run_pipeline: {e}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        print(f"An unexpected error occurred in run_pipeline: {e}")

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
                'generate_visualizations'
            ],
            help="""Specify which steps to run in the pipeline. Options include:
        data_validation             : Validates data before using it.
        automatic_test_model                : Deploys a specified model locally or on a server and test the different parameter configuration.
        test_model                : Deploys a specified model locally or on a server.
        configure_prompt_version        : Tracks and updates the versions of prompts used for testing.
        analyze_results             : Analyzes model test results.
        manage_experiment_logs      : Manages the logs of your experiments.
        generate_visualizations     : Creates visual reports of model performance.

        You can specify multiple steps, e.g., "--run data_validation test_model analyze_results".
        If no steps are provided, the entire pipeline is executed by default."""
        )

        args = parser.parse_args()
        selected_steps = args.run

        logging.info(f'Starting the pipeline with the following steps: {selected_steps}')
        run_pipeline(selected_steps)

    except Exception as e:
        logging.error(f"Unexpected error in {__name__}.main: {e}")
        print(f"An unexpected error occurred in main: {e}")

if __name__ == "__main__":
    main()

