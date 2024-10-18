import json
import logging
from utils import load_config
from datetime import datetime

# Load configuration
config = load_config()

def load_prompt_versions():
    """Load prompt versions from the JSON file located in the metadata folder."""
    try:
        prompt_file_path = config['paths']['system_prompt_versions']
        with open(prompt_file_path, 'r') as file:
            prompt_versions = json.load(file)
        
        # Optional validation to ensure correct structure
        if not all('version' in pv and 'prompt' in pv and 'timestamp' in pv for pv in prompt_versions):
            logging.error("Invalid prompt version format in the file.")
            print("Error: Invalid prompt version format in the file.")
            return []
        
        return prompt_versions
    except FileNotFoundError:
        logging.error(f"Prompt version file {prompt_file_path} not found.")
        print(f"Error: Prompt version file {prompt_file_path} not found.")
        return []
    except json.JSONDecodeError:
        logging.error("Error decoding the prompt version file.")
        print("Error decoding the prompt version file.")
        return []
    except Exception as e:
        logging.error(f"Unexpected error loading prompt versions: {e}")
        print(f"An unexpected error occurred while loading prompt versions: {e}")
        return []

def configure_prompt_version():
    """Interactively configure the prompt version to use based on user selection."""
    prompt_versions = load_prompt_versions()

    if not prompt_versions:
        print("No prompt versions available to configure.")
        return None

    # Display available prompt versions with timestamp formatting
    print("Available prompt versions:")
    for i, system_prompt_version in enumerate(prompt_versions, 1):
        # Parsing the timestamp to a more readable format
        timestamp_str = system_prompt_version.get('timestamp')
        try:
            timestamp = datetime.fromisoformat(timestamp_str).strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            timestamp = "Invalid timestamp"
        
        print(f"{i}. Version: {system_prompt_version['version']} - Prompt: {system_prompt_version['prompt']} (Timestamp: {timestamp})")

    # Keep prompting the user until a valid choice is made
    while True:
        try:
            prompt_choice = int(input("Enter the number of the prompt version you wish to use: "))
            if 1 <= prompt_choice <= len(prompt_versions):
                selected_prompt_version = prompt_versions[prompt_choice - 1]
                print(f"Selected prompt version: {selected_prompt_version['version']}")
                return selected_prompt_version
            else:
                print("Invalid choice. Please enter a number corresponding to the available prompt versions.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")


# Log message example when defaulting to version 1.0
def log_default_prompt_version(selected_version):
    if selected_version is None:
        logging.warning("No prompt version selected. Defaulting to version 1.0.")
        print("No prompt version selected. Defaulting to version 1.0.")
