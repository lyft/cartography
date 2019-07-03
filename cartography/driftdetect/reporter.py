def report_drift(drift_info_detector_pairs, new=True):
    """
    Prints Drift Information

    :type drift_info_detector_pairs: List of Tuples of the form (Dictionary, DriftState)
    :param drift_info_detector_pairs: Drift information
    :return: None
    """

    if new:
        print("New Drift Information:")
        print()
    else:
        print("Missing Drift Information:")
        print()

    for drift_info, detector in drift_info_detector_pairs:
        print("Detector Name:", detector.name)
        print("Drift Information:", drift_info)
        print()
