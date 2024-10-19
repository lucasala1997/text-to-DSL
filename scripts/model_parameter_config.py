import json
import logging
from utils import load_config

# Load configuration
try:
    config = load_config()
except Exception as e:
    logging.error(f"Error loading config in {__name__}: {e}")
    print(f"An unexpected error occurred while loading config: {e}")

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

        # Read-only fields outside the "parameters" key
        read_only_fields = [
            "model_name", "ollama_command", "vram_requirement", "type", "supported", "deployment_type"
        ]

        # Read-only fields inside the "parameters" key
        parameters_read_only_fields = ["seed", "num_predict", "num_ctx"]

        # Display current parameters and allow updates only on editable fields
        model_data = supported_models[model_name]

        # Display parameters (editable and read-only)
        if "parameters" in model_data:
            for key, value in model_data["parameters"].items():
                if key in parameters_read_only_fields:
                    print(f"{key}: {value} (read-only)")
                else:
                    while True:  # Keep asking until a valid value is provided
                        new_value = input(f"{key} (current: {value}) [Press Enter to keep current]: ").strip()

                        # Enforce constraints for specific parameters
                        if new_value:
                            if key == "temperature":
                                try:
                                    new_value = float(new_value)
                                    if 0 <= new_value <= 1:
                                        model_data["parameters"][key] = new_value
                                        break
                                    else:
                                        raise ValueError
                                except ValueError:
                                    print("Invalid value. Temperature must be between 0 and 1. Please try again.")
                            elif key == "top_k":
                                try:
                                    new_value = int(new_value)
                                    if 10 <= new_value <= 100:
                                        model_data["parameters"][key] = new_value
                                        break
                                    else:
                                        raise ValueError
                                except ValueError:
                                    print("Invalid value. Top_k must be an integer between 10 and 100. Please try again.")
                            elif key == "top_p":
                                try:
                                    new_value = float(new_value)
                                    if 0.5 <= new_value <= 0.95:
                                        model_data["parameters"][key] = new_value
                                        break
                                    else:
                                        raise ValueError
                                except ValueError:
                                    print("Invalid value. Top_p must be between 0.5 and 0.95. Please try again.")
                            else:
                                # For non-constrained fields, just update the value
                                try:
                                    new_value = eval(new_value)  # Convert to correct data type if possible
                                except (NameError, SyntaxError):
                                    pass  # Leave as string if conversion fails
                                model_data["parameters"][key] = new_value
                                break
                        else:
                            break  # Keep the current value if the user presses Enter

        # Save the updated configurations back to the JSON file
        with open(config_file, 'w') as file:
            json.dump(model_configs, file, indent=4)

        logging.info(f"Parameters for model {model_name} configured successfully.")

        return model_data
    
    except FileNotFoundError as fnfe:
        logging.error(f"Model configuration file {config_file} not found: {fnfe}")
        print(f"Error: Model configuration file {config_file} not found.")
    except json.JSONDecodeError as jde:
        logging.error(f"Error decoding the model configuration file: {jde}")
        print("Error decoding the model configuration file.")
    except Exception as e:
        logging.error(f"Unexpected error in {__name__}.configure_model_parameters: {e}")
        print(f"An unexpected error occurred in configure_model_parameters: {e}")
