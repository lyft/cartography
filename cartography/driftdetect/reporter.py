def report_drift(drift_info_detector_pairs, new=True):
    """
    Report drift
    :param drift_info_detector_pairs: Drift information
    :return: None
    """

    if new:
        print("New Drift Information")
    else:
        print("Missing Drift Information")

    for drift_info, detector in drift_info_detector_pairs:
        print("Detector Name:", detector.name)
        print("Detector Type:", str(detector.detector_type))
        print("Drift Information:", drift_info)
        print()
