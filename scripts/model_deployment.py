import logging
import subprocess
import os
from utils import load_config

# Load configuration
config = load_config()
# Use the OpenAI API key securely
# os.environ['OPENAI_API_KEY'] = config['openai_key']

def deploy_model(model_namee):
    """Deploys a specified model either locally or through a remote API.

    Args:
        model_name (str): The name of the model to deploy.
    Returns:
        bool: True if the model is successfully deployed, False otherwise.
    """
    try:
        if model_type == 'local':
            deploy_command = ['ollama', 'deploy', model_name]
            if quantization:
                deploy_command.extend(['--quantization', quantization])
            if precision == 'quantized':
                deploy_command.append('--precision quantized')
            
            logging.info(f"Attempting to deploy local model: {model_name} with precision: {precision} and quantization: {quantization}")
            subprocess.run(deploy_command, check=True)

        elif model_type == 'remote':
            logging.info(f"Deploying OpenAI model: {model_name}")

        else:
            raise ValueError("Invalid model type. Choose 'local' or 'remote'.")

        logging.info(f"Model {model_name} deployed successfully.")
        return True

    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to deploy model {model_name}: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error during model deployment: {e}")
        return False
