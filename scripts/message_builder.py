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

    # Include grammar rules
    message = f"Rules that need to be followed to write the code:\n{grammar}\n\n"

    # TODO: Include separators
    message += f"################\n"

    # Include few-shot examples if any
    if few_shot_examples:
        message += "Examples:\n"
        for idx, ex in enumerate(few_shot_examples, 1):
            message += f"Example {idx}:\n"
            message += f"Question: {ex['input_text']}\n"
            message += f"Answer: {ex['expected_dsl_output']}\n\n"

    message += f"################\n"
    # Append the specific example to be processed

    #TODO: it is needed?
    message += "convert the following sentence.\n"

    # Append the specific description of a DSL to be processed
    message += nl_dsl

    print("______________Begin of the prompt________________")
    print(message)
    print("______________End of the prompt________________")
    return message
