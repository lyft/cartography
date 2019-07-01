def report_drift(drift_info_detector_pairs):
    """
    Report drift
    :param drift_info_detector_pairs: Drift information
    :return: None
    """
    for drift_info, detector in drift_info_detector_pairs:
        print("Detector Name:", detector.name)
        print("Detector Type:", str(detector.detector_type))
        print("Drift Information:", drift_info)
        print()
