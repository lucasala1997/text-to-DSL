def build_message(model_name, system_prompt, grammar, few_shot_examples, nl_dsl):
    """
    Constructs a message for a language model based on the provided parameters.

    Args:
        model_name (str): The name of the model.
        system_prompt (str): The system prompt for the message.
        grammar (str): The grammar rules or guidelines.
        few_shot_examples (list): A list of few-shot examples.
        example (str): The specific example to be processed.

    Returns:
        str: A formatted message based on the given parameters.
    """

    # TODO: Implement the message construction logic for each model (if needed)
    # TODO: Create a dict of models and separators

    message = ""
    if model_name == "Claude 3.5 sonnet":
        # Add system prompt if available
        if system_prompt:
            message += f"{system_prompt}\n\n"

        # Start with "Human:" turn
        message += f"Human: Rules that need to be followed to write the code:\n{grammar}\n\n"

        # Add few-shot examples
        if few_shot_examples:
            for idx, ex in enumerate(few_shot_examples, 1):
                message += f"Human: {ex['input_text']}\n"
                message += f"Assistant: {ex['expected_dsl_output']}\n\n"

        # Add the final user input (question)
        message += f"Human: {nl_dsl}\n\nAssistant:"
    
    else:
        # General message construction for other models
        message += f"Rules that need to be followed to write the code:\n{grammar}\n\n"
        message += f"###\n"
        
        if few_shot_examples:
            for idx, ex in enumerate(few_shot_examples, 1):
                message += f"Example {idx}:\n"
                message += f"Question: {ex['input_text']}\n"
                message += f"Answer: {ex['expected_dsl_output']}\n\n"
        
        message += f"###\n\n"
        message += f"Question: {nl_dsl}\n"
        message += f"Answer:"
    
    return message
