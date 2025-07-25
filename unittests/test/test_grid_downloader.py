# Copyright Robert Malovec (github@malovec.sk)
# Licensed under Apache-2.0 (http://www.apache.org/licenses/LICENSE-2.0)

import pytest
import os
import requests
from unittest.mock import MagicMock, patch
from GridDownloader import GridDownloader
from SeleniumLibrary.keywords.browsermanagement import BrowserManagementKeywords
from robot.libraries.BuiltIn import RobotNotRunningError

"""
GridDownloaderTest
    Covers GridDownloader methods
"""


@pytest.fixture
def mock_context():
    # Mocking the context object passed to the class
    return MagicMock()


@pytest.fixture
def grid_downloader(mock_context):
    # Instantiate GridDownloader with activate_capability="Yes"

    grid_downloader = GridDownloader(mock_context, activate_capability="Yes")

    mock_command_executor = MagicMock()
    mock_command_executor._url = "http://selenium.grid.com:4444/wd/hub"
    grid_downloader.browser.driver.command_executor = mock_command_executor

    return grid_downloader


@pytest.fixture
def grid_downloader_activate_capability_disabled(mock_context):
    # Instantiate GridDownloader with activate_capability="No"
    return GridDownloader(mock_context, activate_capability="No")


def test_initialization_with_capability_yes(grid_downloader, mock_context):
    # Test that the initialization works when activate_capability is "Yes"

    assert grid_downloader.force_download_capability is True
    assert grid_downloader.browser is not None
    assert grid_downloader.output_dir is not None
    assert isinstance(grid_downloader.output_dir, str)


def test_initialization_with_capability_no(grid_downloader_activate_capability_disabled, mock_context):
    # Test that the initialization works when activate_capability is "No"

    assert grid_downloader_activate_capability_disabled.force_download_capability is False
    assert grid_downloader_activate_capability_disabled.browser is not None
    assert grid_downloader_activate_capability_disabled.output_dir is not None
    assert isinstance(grid_downloader_activate_capability_disabled.output_dir, str)


def test_browser_initialization(grid_downloader):
    # Test that the browser is initialized correctly

    assert grid_downloader.browser is not None
    assert isinstance(grid_downloader.browser, BrowserManagementKeywords)


def test_get_rf_output_dir_robot_running(grid_downloader):
    # Test output directory retrieval when Robot Framework is running

    with patch("robot.libraries.BuiltIn.BuiltIn.get_variable_value", return_value="/robot/output"):
        output_dir = grid_downloader._get_rf_output_dir()
        assert output_dir == "/robot/output"


def test_get_rf_output_dir_robot_not_running(grid_downloader):
    # Test output directory retrieval when Robot Framework is not running

    with patch("robot.libraries.BuiltIn.BuiltIn.get_variable_value", side_effect=RobotNotRunningError):
        with patch("os.getcwd", return_value="/current/dir"):
            output_dir = grid_downloader._get_rf_output_dir()
            pytest.raises(RobotNotRunningError)
            assert output_dir == os.getcwd()


@patch('requests.get')
def test_get_list_of_downloaded_files_success(mock_requests_get, grid_downloader):
    # Test successful retrieval of the available file list

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "value": {
            "names": ["file1.txt", "file2.txt"]
        }
    }
    mock_requests_get.return_value = mock_response

    # Call the method
    files = grid_downloader.get_list_of_downloaded_files()

    # Assert the expected results
    assert files == ["file1.txt", "file2.txt"]
    mock_requests_get.assert_called_once_with(grid_downloader._get_downloader_endpoint(), timeout=600, verify=False)


@patch('requests.get')
def test_get_list_of_downloaded_files_failure(mock_requests_get, grid_downloader):
    # Test failure to retrieve the available file list

    mock_requests_get.side_effect = Exception("Network error")

    # Expect AssertionError to be raised
    with pytest.raises(AssertionError,
                       match="Failed to get list of downloaded files. Set 'se:downloadsEnabled' capability."):
        grid_downloader.get_list_of_downloaded_files()

    mock_requests_get.assert_called_once_with(grid_downloader._get_downloader_endpoint(), timeout=600, verify=False)


@patch('requests.post')
def test_download_file_from_grid_file_not_found(mock_requests_post, grid_downloader):
    # Test download attempt of not available file

    mock_response = MagicMock()
    mock_response.status_code = requests.codes.internal_server_error
    mock_response.content = b"Cannot find file"
    mock_requests_post.return_value = mock_response

    # Expect an assertion error due to file not being found
    with pytest.raises(AssertionError, match="Failed to download non_existent_file.txt. File not found."):
        grid_downloader.download_file_from_grid("non_existent_file.txt")


@patch('requests.post')
def test_download_file_from_grid_network_failure(mock_requests_post, grid_downloader):
    # Test download attempt of file with network failure

    mock_requests_post.side_effect = Exception("Network error")

    # Expect an exception to be raised
    with pytest.raises(Exception, match="Failed to download test_file.txt."):
        grid_downloader.download_file_from_grid("test_file.txt")


@patch('requests.post')
def test_download_file_from_grid(mock_requests_post, grid_downloader):
    # Test successful download of a file and file content extraction

    mock_response = MagicMock()
    mock_response.status_code = requests.codes.ok
    mock_response.json.return_value = {
        "value": {
            "filename": "file.txt",
            "contents": "UEsDBBQACAAIAHRNUFkAAAAAAAAAAAwAAAAIACAAZmlsZS50eHRVVA0AB6xuD2eubg9nrG4PZ3V4CwABBPUBAAA"
                        + "EFAAAAPNIzcnJVyjPL8pJ4QIAUEsHCNXgObcOAAAADAAAAFBLAQIUAxQACAAIAHRNUFnV4Dm3DgAAAAwAAAAIAC"
                        + "AAAAAAAAAAAACkgQAAAABmaWxlLnR4dFVUDQAHrG4PZ65uD2esbg9ndXgLAAEE9QEAAAQUAAAAUEsFBgAAAAABA"
                        + "AEAVgAAAGQAAAAAAA=="
        }
    }
    mock_requests_post.return_value = mock_response

    # Expect an assertion error due to file not being found
    content = grid_downloader.download_file_from_grid("file.txt")
    assert content == b"Hello world\n"


@patch('SeleniumLibrary.keywords.browsermanagement.BrowserManagementKeywords.open_browser')
def test_open_browser_download_capability_enabled_no_options(mock_open_browser, grid_downloader):
    # Test that the download capability is automatically added to the empty browser options

    mock_open_browser.return_value = "Browser opened"

    # Set up kwargs with no "options"
    kwargs = {}

    # Call the method with download capability enabled
    grid_downloader.open_browser("https://selenium.dev", **kwargs)

    # Assert that the download capability was added to the options
    assert BrowserManagementKeywords.open_browser.called
    assert (BrowserManagementKeywords.open_browser.call_args[1]["options"] ==
            'set_capability("se:downloadsEnabled", True)')


@patch('SeleniumLibrary.keywords.browsermanagement.BrowserManagementKeywords.open_browser')
def test_open_browser_download_capability_enabled(mock_open_browser, grid_downloader):
    # Test that the download capability is automatically added to the browser options

    mock_open_browser.return_value = "Browser opened"

    # Set up kwargs with no "options"
    kwargs = {"options": "platform_name=WINDOWS"}

    # Call the method with download capability enabled
    grid_downloader.open_browser("https://selenium.dev", **kwargs)

    # Assert that the download capability was added to the options
    assert BrowserManagementKeywords.open_browser.called
    assert (BrowserManagementKeywords.open_browser.call_args[1]["options"] ==
            'platform_name=WINDOWS;set_capability("se:downloadsEnabled", True)')


@patch('SeleniumLibrary.keywords.browsermanagement.BrowserManagementKeywords.open_browser')
def test_open_browser_download_capability_disabled(mock_open_browser, grid_downloader_activate_capability_disabled):
    # Test that the download capability is not added to the browser options when capability activation disabled

    mock_open_browser.return_value = "Browser opened"

    # Set up kwargs with no "options"
    kwargs = {"options": "platform_name=WINDOWS"}

    # Call the method with download capability enabled
    grid_downloader_activate_capability_disabled.open_browser("https://selenium.dev", **kwargs)

    # Assert that the download capability was added to the options
    assert BrowserManagementKeywords.open_browser.called
    assert (BrowserManagementKeywords.open_browser.call_args[1]["options"] ==
            'platform_name=WINDOWS')
