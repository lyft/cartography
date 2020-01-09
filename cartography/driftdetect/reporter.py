def report_drift_new(results, state_properties):
    """
    Prints new additions in Query Results between two states.

    :type results: List of List of Strings.
    :param results: Deviation information.
    :return: None
    """
    print("New Query Results:")
    print()
    for result in results:
        for field, value in zip(state_properties, result):
            print(field, ": ", value)
        print()


def report_drift_missing(results, state_properties):
    """
    Prints missing results in Query Results between two states.

    :type results: List of List of Strings.
    :param results: Deviation information.
    :return: None
    """
    print("Missing Query Results:")
    print()
    for result in results:
        for field, value in zip(state_properties, result):
            print(field, ": ", value)
        print()


def report_drift(new_results, missing_results, state_name, state_properties):
    """
    Prints the results between two states.
    :param new_results: List of new results.
    :param missing_results: List of missing results.
    :param state_name: Query Name.
    :param state_properties: Query Properties.
    :return: None.
    """
    print("Query Name: ", state_name)
    print()
    if new_results:
        report_drift_new(new_results, state_properties)
    print()
    if missing_results:
        report_drift_missing(missing_results, state_properties)
