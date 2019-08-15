import logging
import pathlib

logger = logging.getLogger(__name__)


def valid_directory(directory):
    """
    Error handling for validating directory.

    :type directory: string
    :param directory: Path to directory.
    :return:
    """
    if not directory:
        logger.info("Cannot perform drift-detection because no job path was provided.")
        return False
    drift_detection_directory = pathlib.Path(directory)
    if not drift_detection_directory.exists():
        logger.warning(
            "Cannot perform drift-detection because the provided job path '%s' does not exist.",
            drift_detection_directory,
        )
        return False
    if not drift_detection_directory.is_dir():
        logger.warning(
            "Cannot perform drift-detection because the provided job path '%s' is not a directory.",
            drift_detection_directory,
        )
        return False
    return True


def load_object(storage, schema, fp):
    """
    Loads and returns an object from a file path.
    :param storage: Storage Object.
    :param schema: Serializer.
    :param fp: File Path.
    :return: Object
    """
    data = storage.load(fp)
    obj = schema.load(data)
    return obj


def store_object(storage, schema, fp, obj):
    """
    Stores an object to a file path.
    :param storage: Storage Object.
    :param schema: Serializer.
    :param fp: File Path.
    :param obj: Object to be stored
    :return:
    """
    data = schema.dump(obj)
    storage.write(data, fp)


def transform_results(results, state):
    """
    Transforms results from lists to dictionaries.
    :param results: Results.
    :param state: State object.
    :return: List of Dictionary Results.
    """
    transformed_results = []
    for result in results:
        drift_dict = {}
        for key, value in zip(state.properties, result):
            drift_dict[key] = value
        transformed_results.append(drift_dict)
    return transformed_results
