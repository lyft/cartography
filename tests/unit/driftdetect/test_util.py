from unittest.mock import MagicMock

from cartography.driftdetect.util import load_object
from cartography.driftdetect.util import store_object


def test_load_object():
    storage = MagicMock()
    schema = MagicMock()
    fp = MagicMock()
    data = MagicMock()
    storage.load.return_value = data
    load_object(storage, schema, fp)
    storage.load.assert_called_with(fp)
    schema.load.assert_called_with(data)


def test_write_object():
    storage = MagicMock()
    schema = MagicMock()
    fp = MagicMock()
    obj = MagicMock()
    data = MagicMock()
    schema.dump.return_value = data
    store_object(storage, schema, fp, obj)
    schema.dump.assert_called_with(obj)
    storage.write.assert_called_with(data, fp)
