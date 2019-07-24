
def report_drift_new(deviation_state_pairs):
    """
    Prints new additions in Query Results between two states.

    :type deviation_state_pairs: List of Tuples of the form (Dictionary, State)
    :param deviation_state_pairs: Deviation information
    :return: None
    """
    print("New Query Results:")
    print()
    report_drift(deviation_state_pairs)


def report_drift_missing(deviation_state_pairs):
    """
    Prints missing results in Query Results between two states.

    :type deviation_state_pairs: List of Tuples of the form (Dictionary, State)
    :param deviation_state_pairs: Deviation information
    :return: None
    """
    print("Missing Query Results:")
    print()
    report_drift(deviation_state_pairs)


def report_drift(deviation_state_pairs):
    """
    Prints the results in drift_info between two states.

    :type deviation_state_pairs: List of Tuples of the form (Dictionary, State)
    :param deviation_state_pairs: Deviation information
    :return: None
    """
    for drift_info, detector in deviation_state_pairs:
        print("Query Name:", detector.name)
        print("Result Information:", drift_info)
        for key, value in drift_info.items():
            print(key, "|", value)
        print()
