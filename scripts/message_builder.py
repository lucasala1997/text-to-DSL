import logging
from utils import load_config


config = load_config()
# Set up logging based on config.json
logging.basicConfig(
    filename=config['paths']['project_log_file'],
    level=getattr(logging, config['logging']['level'], logging.INFO),
    format=config['logging']['format']
)

def build_message(model_name, system_prompt, grammar, few_shot_examples, nl_dsl):
    """
    Constructs a message for a language model based on the provided parameters,
    including the grammar in the system prompt for better model guidance.

    Args:
        model_name (str): The name of the model.
        system_prompt (str): The system prompt for the message.
        grammar (str): The grammar rules or guidelines.
        few_shot_examples (list): A list of few-shot examples.
        nl_dsl (str): The specific example to be processed.

    Returns:
        list or str: A formatted message based on the given parameters.
    """
    if model_name == "Claude 3.5 sonnet":
        message = ""
        # Combine system prompt and grammar
        if system_prompt or grammar:
            system_content = f"{system_prompt}\n\nRules that need to be followed to write the code:\n{grammar}"
            message += f"{system_content}\n\n"

        # Start with "Human:" turn
        # Add few-shot examples
        if few_shot_examples:
            for ex in few_shot_examples:
                message += f"Human: {ex['input_text']}\n"
                message += f"Assistant: {ex['expected_dsl_output']}\n\n"

        # Add the final user input
        message += f"Human: {nl_dsl}\n\nAssistant:"

    else:
        message = []
        # Combine system prompt and grammar in the system message
        if system_prompt or grammar:
            system_content = f"{system_prompt}\n\nRules that need to be followed to write the code:\n{grammar}"
            message.append({"role": "system", "content": system_content})
            print("The model has prompt and grammar")
        else:
            message.append({"role": "system", "content": system_prompt})

        # Add few-shot examples with alternating roles
        if few_shot_examples:
            for example in few_shot_examples:
                message.append({"role": "user", "content": example['input_text']})
                message.append({"role": "assistant", "content": example['expected_dsl_output']})

        # Final user input
        message.append({"role": "user", "content": nl_dsl})

    return message
