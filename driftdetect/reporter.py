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
            print(detector.name, str(detector.detector_type))
            for key, value in drift_info.items():
                print(key, value)
