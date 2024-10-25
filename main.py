import logging
import argparse
import traceback  # Module to log exceptions
from utils import load_config
from scripts.data_validation import validate_data
from scripts.model_parameter_config import configure_model_parameters
from scripts.prompt_version import configure_prompt_version
from scripts.model_testing import test_model
from scripts.result_analysis import analyze_results
import tensorflow as tf

# from scripts.experiment_log_manager import manage_experiment_logs
# from scripts.visualization_reporting import generate_visualizations

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
    logging.basicConfig(
        filename=config['paths']['project_log_file'],
        level=config['logging']['level'],
        format=config['logging']['format']
    )
except Exception as e:
    logging.error(f"Error setting up logging in {__name__}: {e}")
    logging.error(f"Traceback: {traceback.format_exc()}")  # Log the detailed traceback
    print(f"An unexpected error occurred while setting up logging: {e}")

def deploy_selected_model(dataset_name, system_prompt_version=None):
    try:
        """Handles the deployment of the selected model using the latest parameters."""
        selected_model = configure_model_parameters()

        if selected_model:
            selected_model_name = selected_model.get('model_name')  # Extract the model name
            print(f"\nDeploying and prompting the model: {selected_model_name}")
            if test_model(dataset_name, selected_model_name, system_prompt_version):
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

    dataset_name = "GIS"
    try:
        if 'data_validation' in selected_steps:
            print('Starting data validation...')
            logging.info('Starting data validation...')
            dataset_name = validate_data()
            print('Data validated successfully.')
            print('--------------------------')

        if 'configure_prompt_version' in selected_steps:
            print('Updating prompt versions...')
            logging.info('Updating prompt versions...')
            prompt_version = configure_prompt_version()
            print(f"Selected prompt version: {prompt_version}")
            print('--------------------------')

        if 'test_model' in selected_steps:
            print('Deploying models...')
            logging.info('Deploying models...')
            #if the user decide to not execute the configure_prompt_version step, the prompt_version will be None (default value)
            deploy_selected_model(dataset_name, prompt_version) if prompt_version else deploy_selected_model(dataset_name)
            print('--------------------------')


        # if 'analyze_results' in selected_steps:
        #     print('Analyzing results...')
        #     logging.info('Analyzing results...')
        #     analyze_results()
        #     print('Analysis saved.')
        #     print('--------------------------')

        # if 'generate_visualizations' in selected_steps:
        #     logging.info('Generating visualizations...')
        #     generate_visualizations()

        logging.info('Process completed successfully.')
        print('Process completed successfully.')

    except Exception as e:
        logging.error(f"Unexpected error in {__name__}.run_pipeline: {e}")
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
                'data_validation', 'configure_prompt_version', 'test_model', 'analyze_results', 'manage_experiment_logs',
                'generate_visualizations'
            ],
            help="""Specify which steps to run in the pipeline. Options include:
        data_validation             : Validates data before using it.
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
