
def steps_to_list(string_literal):
    """Takes a comma separated list and returns a list data type."""
    new_list = []

    for item in string_literal.split(','):
        new_list.append(item)

    return new_list
