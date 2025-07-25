*** Settings ***
Documentation     Selenium Library Grid Downloader Plugin e2e tests
Library   SeleniumLibrary  plugins=GridDownloader

Test Teardown  Close All Browsers


*** Variables ***
${DOWNLOAD_URL}           https://www.selenium.dev/selenium/web/downloads/download.html
${DOWNLOAD_LINK}          file-1
${FILENAME}               file_1.txt

${BROWSER}                chrome
${options}                platform_name="windows"
${SELENIUM_GRID_HUB_URL}  https://selenium.grid.com:4444/wd/hub
${WAIT_TIMEOUT}           5 seconds


*** Test Cases ***
Download two files
   Launch Browser
   Wait Until Element Is Visible  ${DOWNLOAD_LINK}
   Click Element  ${DOWNLOAD_LINK}
   Wait Until File Is Available To Download  ${FILENAME}
   Get List Of Downloaded Files
   ${content}=  Download File From Grid  ${FILENAME}
   Log  Content is: ${content}


*** Keywords ***
Launch Browser
   [Documentation]  Start specified browser using remote grid
   Open Browser
   ...  ${DOWNLOAD_URL}
   ...  ${BROWSER}
   ...  remote_url=${SELENIUM_GRID_HUB_URL}
   ...  options=${options}
