from cartography import util


def test_run_analysis_job_default_package(mocker):
    mocker.patch('cartography.util.GraphJob')
    read_text_mock = mocker.patch('cartography.util.read_text')
    util.run_analysis_job('test.json', mocker.Mock(), mocker.Mock())
    read_text_mock.assert_called_once_with('cartography.data.jobs.analysis', 'test.json')


def test_run_analysis_job_custom_package(mocker):
    mocker.patch('cartography.util.GraphJob')
    read_text_mock = mocker.patch('cartography.util.read_text')
    util.run_analysis_job('test.json', mocker.Mock(), mocker.Mock(), package='a.b.c')
    read_text_mock.assert_called_once_with('a.b.c', 'test.json')
