import json
import logging
from utils import load_config

# Load configuration
config = load_config()

def load_prompt_versions():
    """Load prompt versions from the JSON file located in the metadata folder."""
    try:
        prompt_file_path = config['paths']['prompt_versions_file']
        with open(prompt_file_path, 'r') as file:
            prompt_versions = json.load(file)
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

    # Display available prompt versions
    print("Available prompt versions:")
    for i, prompt_version in enumerate(prompt_versions, 1):
        print(f"{i}. Version: {prompt_version['version']} - Prompt: {prompt_version['prompt']}")

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
