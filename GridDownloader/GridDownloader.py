# Copyright Robert Malovec (github@malovec.sk)
# Licensed under Apache-2.0 (http://www.apache.org/licenses/LICENSE-2.0)

"""
This module provides functionalities for downloading files from remote Selenium Grid web testing node.
"""

# The rest of your imports and code here


import os
import io
import zipfile
import base64
from time import sleep
from urllib.parse import urlparse
import requests
from SeleniumLibrary.base import LibraryComponent, keyword
from SeleniumLibrary.keywords.browsermanagement import BrowserManagementKeywords
from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn, RobotNotRunningError


class GridDownloader(LibraryComponent):
    """
    `GridDownloader` is a SeleniumLibrary Plugin that interacts with a Selenium Grid instance to download files
    from the remote test machine to the local machine.

    It provides functionality to enable file downloads on the remote grid, download files, list files, and wait for
    files to be available for download.

    == Usage ==

    Example import with automatic download browser capability enablement:
    | ***** Settings *****
    |
    | Library   SeleniumLibrary    plugins=GridDownloader


    Example import without automatic browser capability enablement:
    | ***** Settings *****
    |
    | Library   SeleniumLibrary    plugins=GridDownloader;activate_capability=No

    If automatic download browser capability enablement is disabled you need to set this capability manually
    in your browser options.

    == Example - automatic capability activation ENABLED ==

    | *** Settings ***
    |
    | Library   SeleniumLibrary  plugins=GridDownloader
    |
    | Test Teardown  Close All Browsers
    |
    |
    | *** Variables ***
    |
    | ${BROWSER}        chrome
    | ${URL}            https://www.example.com
    | ${options}        platform_name="windows"
    | ${GRID_URL}       http://grid.com:4444/wd/hub
    | ${DOWNLOAD_LINK}  xpath=//a[@id='download']
    | ${FILENAME}       file1.txt
    |
    | *** Test Cases ***
    |
    | Download File From Grid
    |    Open Browser    ${URL}    ${BROWSER}    remote_url=${GRID_URL}    options=${options}
    |    Click Element   ${DOWNLOAD_LINK}
    |    Wait Until File Is Available To Download  ${FILENAME}
    |    Get List Of Downloaded Files
    |    ${content}=  Download File From Grid  ${FILENAME}
    |    Should Be Equal As Strings  ${content}  Hello world

    == Example - automatic capability activation DISABLED ==

    | *** Settings ***
    |
    | Library   SeleniumLibrary  plugins=GridDownloader;activate_capability=No
    |
    | Test Teardown  Close All Browsers
    |
    |
    | *** Variables ***
    |
    | ${BROWSER}        chrome
    | ${URL}            https://www.example.com
    | ${options}        platform_name="windows";set_capability("se:downloadsEnabled", True)
    | ${GRID_URL}       http://grid.com:4444/wd/hub
    | ${DOWNLOAD_LINK}  xpath=//a[@id='download']
    | ${FILENAME}       file1.txt
    |
    | *** Test Cases ***
    |
    | Download File From Grid
    |    Open Browser    ${URL}    ${BROWSER}    remote_url=${GRID_URL}    options=${options}
    |    Click Element   ${DOWNLOAD_LINK}
    |    Wait Until File Is Available To Download  ${FILENAME}
    |    Get List Of Downloaded Files
    |    ${content}=  Download File From Grid  ${FILENAME}
    |    Should Be Equal As Strings  ${content}  Hello world
    """

    DOWNLOADS_CAPABILITY = 'set_capability("se:downloadsEnabled", True)'
    WAIT_TIMEOUT = 30
    WAIT_STEP = 2
    REQ_TIMEOUT = 600

    def __init__(self, ctx, activate_capability: str = "Yes"):
        """
        Initializes the GridDownloader library.

        === Arguments details ===

        `ctx`: SeleniumLibrary context.

        `activate_capability`: If set to "Yes", the library will automatically activate the download capability
                                    on the browser.
        """
        # pylint:disable=E1101
        requests.packages.urllib3.disable_warnings()

        LibraryComponent.__init__(self, ctx)
        self.browser = BrowserManagementKeywords(ctx)
        self.output_dir = self._get_rf_output_dir()

        self.force_download_capability = False
        if activate_capability.lower() == "yes":
            self.force_download_capability = True

    @keyword
    def open_browser(self, *args, **kwargs):
        """
        Opens a browser using SeleniumLibrary original keyword with the given arguments and enables file downloading
        capability on the Selenium Grid.

        If `activate_capability` is set to "Yes" during initialization, this keyword automatically adds
        the download capability to the browser options.

        SeleniumLibrary *Open Browser* documentation can be seen
        [https://robotframework.org/SeleniumLibrary/SeleniumLibrary.html#Open%20Browser|here].

        === Usage examples ===

        | Open Browser | https://www.example.com | chrome | options=platform_name="WINDOWS" |
        """
        if self.force_download_capability:

            options_found = False
            if "options" in kwargs:
                options_found = True
                if "se:downloadsEnabled" not in kwargs["options"]:
                    kwargs["options"] += f";{self.DOWNLOADS_CAPABILITY}"

            if not options_found:
                kwargs["options"] = self.DOWNLOADS_CAPABILITY

        self.browser.open_browser(*args, **kwargs)

    # pylint:disable=too-many-locals
    @keyword
    def download_file_from_grid(self, filename, save_path=None, verify=False):
        """
        Downloads a file from the remote Selenium Grid node to the local machine.

        === Arguments details ===

        `filename`: Name of the file to download.

        `save_path`: Local path where the file should be saved.
                          If not provided, Robot Framework's output directory is used.

        `verify`: If False, SSL certificate verification will be disabled for the Selenium Grid endpoint.

        === Usage examples ===

        | Download File From Grid | example.txt |
        | Download File From Grid | example.txt | /local/path |
        | ${file_content}=  Download File From Grid | example.txt |
        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
        }

        data = {"name": f"{filename}"}

        if not save_path:
            save_path = self.output_dir

        url = self._get_downloader_endpoint()

        try:
            response = requests.post(url, headers=headers, json=data, timeout=self.REQ_TIMEOUT, verify=verify)
            # pylint: disable=E1101
            if response.status_code == requests.codes.OK:
                response_json = response.json()
                contents = response_json["value"]["contents"]

                # Extract file content
                zip_content = base64.b64decode(contents)
                with io.BytesIO(zip_content) as zip_buffer:
                    with zipfile.ZipFile(zip_buffer, "r") as zip_ref:
                        unzipped_filename = zip_ref.namelist()[0]
                        with zip_ref.open(unzipped_filename) as unzipped_file:
                            file_content = unzipped_file.read()

                with open(os.path.join(save_path, unzipped_filename), "wb") as output_file:
                    output_file.write(file_content)

                logger.info(f"File {unzipped_filename} downloaded successfully.")
            else:
                logger.debug(f"Failed to download {filename}: {response.status_code}: {response.content}")
                if "cannot find file" in response.content.decode("utf-8").lower():
                    raise AssertionError(f"Failed to download {filename}: File not found.")

                raise AssertionError(f"Failed to download {filename}.")

            return file_content

        except Exception as e:
            logger.debug(f"Failed to download {filename}. Set 'se:downloadsEnabled' capability: {e}")

            if "File not found" in str(e):
                # pylint: disable=W0707
                raise AssertionError(f"Failed to download {filename}: File not found.")

            # pylint: disable=W0707
            raise AssertionError(f"Failed to download {filename}. Is 'se:downloadsEnabled' capability set?")

    @keyword
    def get_list_of_downloaded_files(self, verify=False):
        """
        Returns a list of downloaded files from the remote Selenium Grid node.

        === Arguments details ===

        `verify`: If False, SSL certificate verification will be disabled for the Selenium Grid endpoint.

        === Usage examples ===

        | @{files} = | Get List Of Downloaded Files |
        """

        url = self._get_downloader_endpoint()

        try:
            response = requests.get(url, timeout=self.REQ_TIMEOUT, verify=verify)
            logger.debug(f"{response}")
            response.raise_for_status()

            data = response.json()
            files = data["value"]["names"]

            logger.debug(f"List of downloaded files: {files}")

            return files

        except Exception as e:
            logger.debug(f"Failed to get list of downloaded files. Set 'se:downloadsEnabled' capability: {e}")
            # pylint: disable=W0707
            raise AssertionError("Failed to get list of downloaded files. Set 'se:downloadsEnabled' capability.")

    @keyword
    def wait_until_file_is_available_to_download(self, filename, timeout=None, wait_step=None):
        """
        Waits until the file is available to download on the remote Selenium Grid test machine.

        === Arguments details ===

        `filename`: Name of the file to wait for.

        `timeout`: (default is 30 seconds) Maximum time (in seconds) to wait before raising an error.

        `wait_step`: (default is 2 seconds) Time interval (in seconds) between checks.

        === Usage examples ===

        | Wait Until File Is Available To Download | example.txt |
        | Wait Until File Is Available To Download | example.txt | timeout=60 | wait_step=5 |
        """

        timeout = timeout or self.WAIT_TIMEOUT
        timeout = int(timeout)
        wait_step = wait_step or self.WAIT_STEP
        wait_step = int(wait_step)

        # pylint: disable=W0612
        for i in range(timeout):
            downloaded_files = self.get_list_of_downloaded_files()
            if filename in downloaded_files:
                logger.info(f"File {filename} available to download.")
                return
            sleep(wait_step)

        raise AssertionError(f"File {filename} was not available to download in {timeout * wait_step} seconds.")

    def _get_downloader_endpoint(self):
        """
        Returns the endpoint URL for the Selenium Grid file downloader for actual test session
        """
        grid_url = self._get_remote_url()
        session_id = self.browser.get_session_id()
        url = f"{grid_url}/session/{session_id}/se/files"

        return url

    def _get_remote_url(self):
        """
        Returns the remote URL of the Selenium Grid
        """

        url = urlparse(getattr(self.browser.driver.command_executor, "_url", None))
        remote_url = f"{url.scheme}://{url.hostname}:{url.port}"

        logger.debug(f"Remote URL: {remote_url}")

        return remote_url

    @staticmethod
    def _get_rf_output_dir():
        """
        Returns Robot Framework output directory path
        If Robot Framework is not running, returns the current working directory.
        """
        try:
            output_dir = BuiltIn().get_variable_value("${OUTPUT_DIR}")
        except RobotNotRunningError:
            output_dir = os.getcwd()

        return output_dir
