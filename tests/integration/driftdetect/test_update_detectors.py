import time

from cartography.driftdetect.detect_drift import update_detectors


def test_update_detectors(neo4j_session):
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

    filename = [str(date) for date in time.gmtime()]
    filename.append("json")
    update_detectors(neo4j_session, "tests/data/test_update_detectors", filename)
