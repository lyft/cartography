import datetime
import os

from cartography.driftdetect.storage import FileSystem
from cartography.driftdetect.serializers import StateSchema, ShortcutSchema
from cartography.driftdetect.get_states import get_query_state
from cartography.driftdetect.add_shortcut import add_shortcut


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

    query_directory = "tests/data/test_update_detectors/test_detector"
    state_serializer = StateSchema()
    shortcut_serializer = ShortcutSchema()
    storage = FileSystem

    file_1 = str(datetime.datetime(2019, 1, 1, 0, 0, 2)) + ".json"
    file_2 = str(datetime.datetime(2019, 1, 1, 0, 0, 1)) + ".json"

    get_query_state(neo4j_session, query_directory, state_serializer, storage, file_1)
    add_shortcut(FileSystem(), ShortcutSchema(), query_directory, "most-recent", file_1)

    detector_1_data = FileSystem.load(os.path.join(query_directory, file_1))
    detector_1 = state_serializer.load(detector_1_data)

    detector_2_data = FileSystem.load(os.path.join(query_directory, file_2))
    detector_2 = state_serializer.load(detector_2_data)

    assert detector_1.name == detector_2.name
    assert detector_1.validation_query == detector_2.validation_query
    assert detector_1.properties == detector_2.properties
    assert detector_1.results == detector_2.results

    shortcut_data = FileSystem.load(os.path.join(query_directory, "report_info.json"))
    shortcut = shortcut_serializer.load(shortcut_data)
    assert shortcut.shortcuts['most-recent'] == file_1
    shortcut_data = shortcut_serializer.dump(shortcut)
    FileSystem.write(shortcut_data, os.path.join(query_directory, "report_info.json"))
