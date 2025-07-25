# SeleniumLibrary Grid Downloader Plugin

GridDownloader is plugin for SeleniumLibrary which provides
    Selenium Grid remote files downloading capabilities

## Install

```bash
$ pip install -U robotframework-selenium-downloader-plugin
```

## Keywords documentation

Keywords documentation is available [here](doc/keywords.html).

## Example usage

```robotframework
*** Settings ***

Library   SeleniumLibrary  plugins=GridDownloader

Test Teardown  Close All Browsers


*** Variables ***

${BROWSER}           chrome
${URL}               https://www.example.com
${OPTIONS}           platform_name="windows"
${GRID_URL}          http://grid.example.com:4444/wd/hub
${DOWNLOAD_LINK}     xpath=//a[@id='download']
${FILENAME}          file1.txt
${EXPECTED_CONTENT}  Hello World

*** Test Cases ***

Download File And Check Content
    Open Browser    ${URL}    ${BROWSER}    remote_url=${GRID_URL}    options=${OPTIONS}
    Click Element   ${DOWNLOAD_LINK}
    Wait Until File Is Available To Download  ${FILENAME}
    @{downloaded_files}=  Get List Of Downloaded Files
    Should Contain  ${downloaded_files}   ${FILENAME}
    ${content}=  Download File From Grid  ${FILENAME}
    Should Be Equal As Strings  ${content}  ${EXPECTED_CONTENT}
```
