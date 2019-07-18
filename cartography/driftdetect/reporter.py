def report_drift(drift_info_detector_pairs, new=True):
    """
    Prints Differences in Query Results (both new and missing) between two states.

    :type drift_info_detector_pairs: List of Tuples of the form (Dictionary, State)
    :param drift_info_detector_pairs: Drift information
    :type new: bool
    :param new: Whether or not drift information is new or missing.
    :return: None
    """

    if new:
        print("New Query Results:")
        print()
    else:
        print("Missing Query Results:")
        print()

    for drift_info, detector in drift_info_detector_pairs:
        print("Detector Name:", detector.name)
        print("Drift Information:", drift_info)
        print()
