import json
import os
from datetime import datetime
from utils import load_config

# Load configuration
config = load_config()

def append_new_prompt():
    """Append a new system prompt to the system_prompt_version.json file in the metadata folder."""
    prompt_file_path = config['paths']['system_prompt_versions']

    # Check if the file exists, create it if it doesn't
    if not os.path.exists(prompt_file_path):
        print(f"The prompt version file does not exist. Creating a new one at {prompt_file_path}.")
        with open(prompt_file_path, 'w') as file:
            json.dump([], file)  # Create an empty JSON array to start with

    # Load existing prompts from the file
    try:
        with open(prompt_file_path, 'r') as file:
            prompt_versions = json.load(file)
    except json.JSONDecodeError:
        print("Error decoding the prompt version file. Starting with an empty list.")
        prompt_versions = []

    # Get the list of existing versions
    existing_versions = {entry['version'] for entry in prompt_versions}

    # Prompt the user for a unique version number
    while True:
        new_version = input("Enter the version number for the new prompt (e.g., 1.2): ")
        if new_version in existing_versions:
            print(f"Version {new_version} already exists. Please enter a different version number.")
        else:
            break  # Exit the loop if the version is unique

    # Prompt the user for the new prompt details
    new_prompt = input("Enter the text of the new prompt: ")
    new_rationale = input("Enter the rationale for this prompt: ")

    # Create the new prompt entry
    new_prompt_entry = {
        "version": new_version,
        "prompt": new_prompt,
        "rationale": new_rationale,
        "timestamp": datetime.now().isoformat()
    }

    # Append the new prompt to the list
    prompt_versions.append(new_prompt_entry)

    # Save the updated list back to the JSON file
    try:
        with open(prompt_file_path, 'w') as file:
            json.dump(prompt_versions, file, indent=4)
        print(f"New prompt version {new_version} successfully added.")
    except Exception as e:
        print(f"An error occurred while saving the new prompt: {e}")

if __name__ == "__main__":
    append_new_prompt()
