class Reporter:
    @classmethod
    def report_drift(cls, drift_info_detector_pairs):
        """
        Report drift
        :param drift_info: Drift information
        :param detector: Detector that triggered
        :return: None
        """
        for drift_info, detector in drift_info_detector_pairs:
            print("Detector Name:", detector.name)
            print("Detector Type:", str(detector.detector_type))
            print("Drift Information:", drift_info)
            print()
