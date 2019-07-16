import datetime
import os

from cartography.driftdetect.model import load_state_from_json_file
from cartography.driftdetect.get_states import get_query_states
from cartography.driftdetect.report_info import load_report_info_from_json_file, write_report_info_to_json_file


def test_get_state_detectors(neo4j_session):
    data = [
        ["1", "8", ["15", "22", "29"]],
        ["2", "9", ["16", "23", "30"]],
        ["3", "10", ["17", "24", "31"]],
        ["4", "11", ["18", "25", "32"]],
        ["5", "12", ["19", "26", "33"]],
        ["6", "13", ["20", "27", "34"]],
        ["7", "14", ["21", "28", "35"]],
        ["36", "37", ["38", "39", "40"]]
    ]
    ingest_nodes = """
        MERGE (person:Person{test: {test}})
        SET person.test2 = {test2},
        person.test3 = {test3}
        """
    for node in data:
        test = node[0]
        test2 = node[1]
        test3 = node[2]
        neo4j_session.run(
            ingest_nodes,
            test=test,
            test2=test2,
            test3=test3
        )
    root = "tests/data/test_update_detectors/test_detector"

    file_1 = str(datetime.datetime(2019, 1, 1, 0, 0, 2)) + ".json"
    file_2 = str(datetime.datetime(2019, 1, 1, 0, 0, 1)) + ".json"

    get_query_states(neo4j_session, "tests/data/test_update_detectors", file_1)

    detector_1 = load_state_from_json_file(os.path.join(root, file_1))
    detector_2 = load_state_from_json_file(os.path.join(root, file_2))

    assert detector_1.name == detector_2.name
    assert detector_1.validation_query == detector_2.validation_query
    assert detector_1.properties == detector_2.properties
    assert detector_1.results == detector_2.results

    report_info = load_report_info_from_json_file(os.path.join(root, "report_info.json"))
    assert report_info.shortcuts['most-recent'] == file_1
    report_info.shortcuts.pop('most-recent')
    write_report_info_to_json_file(report_info, os.path.join(root, "report_info.json"))
