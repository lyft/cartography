
def report_drift(new_results, missing_results, state):
    """
    Prints the differences between two states.

    :type new_results: List of Dicts
    :param new_results: New results that were added or modified
    :type missing_results: List of Dicts
    :param missing_results: Missing results that were added or modified
    :type state: State Object
    :param state: State Object for a Query
    :return: None
    """
    if new_results or missing_results:
        print("Query Name:", state.name)
    if new_results:
        print("New Query Results:")
        for drift in new_results:
            for key, value in drift.items():
                print(key, "|", value)
            print()
    if missing_results:
        print("Missing Query Results:")
        for drift in missing_results:
            for key, value in drift.items():
                print(key, "|", value)
            print()
