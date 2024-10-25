import os
import json
from dotenv import load_dotenv

def load_config():
    """Loads the project configuration settings from the config.json file and environment variables.

    Returns:
        dict: A dictionary containing all the configuration settings.
    """
    # Load environment variables from the .env file
    load_dotenv()

    # Load the configuration settings from config.json
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r') as file:
        config_data = json.load(file)

    # Add environment variables to the config dictionary for OpenAI and Claude
    config_data['api_keys'] = {
        "openai_key": os.getenv('OPENAI_API_KEY'),
        "claude_key": os.getenv('CLAUDE_API_KEY')  # Added Claude API key
    }

    return config_data
