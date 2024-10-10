import logging
import argparse
from utils import load_config
from scripts.data_validation import validate_data
from scripts.model_parameter_config import configure_model_parameters
from scripts.prompt_version import configure_prompt_version
from scripts.model_testing import test_model
from scripts.result_analysis import analyze_results
from scripts.experiment_log_manager import manage_experiment_logs
from scripts.visualization_reporting import generate_visualizations

# Load configuration
config = load_config()

# Setup logging based on config settings (config.json)
logging.basicConfig(
    filename=config['paths']['project_log_file'],
    level=config['logging']['level'],
    format=config['logging']['format']
)

def deploy_selected_model(system_prompt_version=None):
    """Handles the deployment of the selected model using the latest parameters."""
    # First, configure model parameters (including model selection)
    selected_model = configure_model_parameters()

    # Proceed to deploy the model if configuration was successful
    if selected_model:
        print(f"Deploying the model: {selected_model}")
        test_model(selected_model, system_prompt_version)
        logging.info(f"Model {selected_model} deployed successfully.")

def run_pipeline(selected_steps):
    """Runs the specified steps in the Text-to-DSL project workflow."""
    try:
        # if 'data_validation' in selected_steps:
        #     print('Starting data validation...')
        #     logging.info('Starting data validation...')
        #     validate_data()

        if 'configure_prompt_version' in selected_steps:
            logging.info('Updating prompt versions...')
            prompt_version = configure_prompt_version()

        if 'test_model' in selected_steps:
            print('Deploying models...')
            logging.info('Deploying models...')
            #if the user decide to not execute the configure_prompt_version step, the prompt_version will be None (default value)
            deploy_selected_model(prompt_version) if prompt_version else deploy_selected_model()


        # if 'analyze_results' in selected_steps:
        #     logging.info('Analyzing results...')
        #     analyze_results()

        # if 'manage_experiment_logs' in selected_steps:
        #     logging.info('Managing experiment logs...')
        #     manage_experiment_logs()

        # if 'generate_visualizations' in selected_steps:
        #     logging.info('Generating visualizations...')
        #     generate_visualizations()

        logging.info('Process completed successfully.')

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print(f"An error occurred: {e}. Check the log file for more details.")

def main():
    """Main function to orchestrate the Text-to-DSL project workflow using command-line arguments."""
    parser = argparse.ArgumentParser(description='Text-to-DSL Project Workflow')
    parser.add_argument(
        '--run',
        type=str,
        nargs='+',
        default=[
            'data_validation', 'configure_prompt_version', 'test_model', 
            'test_model', 'analyze_results', 'manage_experiment_logs',
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

if __name__ == "__main__":
    main()
