import json
import logging
from utils import load_config

# Load configuration
try:
    config = load_config()
except Exception as e:
    logging.error(f"Error loading config in {__name__}: {e}")
    print(f"An unexpected error occurred while loading config: {e}")

# Set up logging based on config.json
logging.basicConfig(
    filename=config['paths']['project_log_file'],
    level=getattr(logging, config['logging']['level'], logging.INFO),
    format=config['logging']['format']
)

def automatic_configure_model_parameters(model_name=None, new_parameters=None):
    """
    Configure parameters for a specific model programmatically.

    Args:
        model_name (str): The name of the model to configure.
        new_parameters (dict): A dictionary of new parameters to set.
    """
    try:
        config_file = config['paths']['model_parameters_file']

        # Load existing parameters from the JSON file
        with open(config_file, 'r') as file:
            model_configs = json.load(file)
        
         # Filter models where "supported" is True
        supported_models = {model: params for model, params in model_configs.items() if str(params.get("supported")).lower() == "true"}

        if not supported_models:
            logging.warning("No supported models available for configuration.")
            print("No supported models available for configuration.")
            return None

        # If no model_name is provided, prompt the user to select a model
        if not model_name:
            available_models = list(supported_models.keys())
            logging.info(f"Available supported models: {available_models}")
            print("Available supported models for parameter configuration:")
            for i, model in enumerate(available_models, 1):
                print(f"{i}. {model}")

            while True:
                try:
                    model_choice = int(input("Enter the number of the model you wish to configure: "))
                    if 1 <= model_choice <= len(available_models):
                        model_name = available_models[model_choice - 1]
                        logging.info(f"Selected model: {model_name}")
                        print(f"\nConfiguring parameters for model: {model_name}")
                        break
                    else:
                        print("Invalid choice. Please enter a number corresponding to the available models.")
                except ValueError as ve:
                    logging.error(f"Invalid input in model selection: {ve}")
                    print("Invalid input. Please enter a valid number.")

        # Update parameters
        if new_parameters:
            model_configs[model_name]['parameters']['temperature'] = new_parameters.get('temperature', model_configs[model_name]['parameters'].get('temperature'))
            model_configs[model_name]['parameters']['top_p'] = new_parameters.get('top_p', model_configs[model_name]['parameters'].get('top_p'))
            model_configs[model_name]['parameters']['top_k'] = new_parameters.get('top_k', model_configs[model_name]['parameters'].get('top_k'))
            
            logging.info(f"Updated parameters for model {model_name}: {new_parameters}")


        # Save the updated configurations back to the JSON file
        with open(config_file, 'w') as file:
            json.dump(model_configs, file, indent=4)

        return model_configs[model_name]['model_name']

    except Exception as e:
        logging.error(f"Error in configure_model_parameters: {e}")
        return None
