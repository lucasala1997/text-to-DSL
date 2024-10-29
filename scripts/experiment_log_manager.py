import json
import logging
from utils import load_config


config = load_config()
# Set up logging based on config.json
logging.basicConfig(
    filename=config['paths']['project_log_file'],
    level=getattr(logging, config['logging']['level'], logging.INFO),
    format=config['logging']['format']
)

#TODO: REWRITE
def manage_experiment_logs():
    """Manages the experiment logs by recording each test run, model configurations, and prompts.

    This function updates the experiment_log.json file with new test results.
    """
    try:
        log_entry = create_log_entry()
        with open('logs/experiment_log.json', 'a') as log_file:
            json.dump(log_entry, log_file)
            log_file.write("\n")
        logging.info('Experiment log updated successfully.')

    except Exception as e:
        logging.error(f"Error managing experiment logs: {e}")
