import json
import logging
from utils import load_config

# Load configuration
config = load_config()

def configure_model_parameters(model_name=None):
    """Interactively configure parameters for a specific model and save updates immediately.

    If a model_name is provided, it skips the model selection step and directly updates the given model.

    Args:
        model_name (str, optional): The name of the model to configure. If not provided, prompts user for selection.
    """
    try:
        config_file = config['paths']['model_parameters_file']

        # Load existing parameters from the JSON file
        with open(config_file, 'r') as file:
            model_configs = json.load(file)

        # Filter models where "supported" is "True"
        supported_models = {model: params for model, params in model_configs.items() if params.get("supported") == "True"}

        if not supported_models:
            print("No supported models available for configuration.")
            return None

        # If no model_name is provided, prompt the user to select a model
        if not model_name:
            available_models = list(supported_models.keys())
            print("Available supported models for parameter configuration:")
            for i, model in enumerate(available_models, 1):
                print(f"{i}. {model}")

            # Keep prompting the user until a valid choice is made
            while True:
                try:
                    model_choice = int(input("Enter the number of the model you wish to configure: "))
                    if 1 <= model_choice <= len(available_models):
                        model_name = available_models[model_choice - 1]
                        print(f"\nConfiguring parameters for model: {model_name}")
                        break  # Exit the loop once a valid choice is made
                    else:
                        print("Invalid choice. Please enter a number corresponding to the available models.")
                except ValueError:
                    print("Invalid input. Please enter a valid number.")

        # Fields that should only be displayed (read-only)
        read_only_fields = [
            "model_name", "supported", "ollama_command", "vram_requirement",
            "precision", "quantization", "deployment_type"
        ]

        # Display current parameters and prompt for updates only on editable fields
        print(f"Current parameters for {model_name}:\n")
        for key, value in supported_models[model_name].items():
            if key in read_only_fields:
                print(f"{key}: {value} (read-only)")
            else:
                new_value = input(f"{key} (current: {value}) [Press Enter to keep current]: ")
                if new_value.strip():
                    try:
                        new_value = eval(new_value)  # Convert to correct data type if possible
                    except (NameError, SyntaxError):
                        pass  # Leave as string if conversion fails
                    supported_models[model_name][key] = new_value

        # Save the updated configurations back to the JSON file
        with open(config_file, 'w') as file:
            json.dump(model_configs, file, indent=4)

        logging.info(f"Parameters for model {model_name} configured successfully.")
        print(f"Parameters for model {model_name} have been successfully updated.")

        return supported_models[model_name]  # Return the updated parameters
    
    except FileNotFoundError:
        logging.error(f"Model configuration file {config_file} not found.")
        print(f"Error: Model configuration file {config_file} not found.")
    except json.JSONDecodeError:
        logging.error("Error decoding the model configuration file.")
        print("Error decoding the model configuration file.")
    except Exception as e:
        logging.error(f"Unexpected error in configuring model parameters: {e}")
        print(f"An unexpected error occurred: {e}")
