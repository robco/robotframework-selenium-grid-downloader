# Copyright Robert Malovec (github@malovec.sk)
# Licensed under Apache-2.0 (http://www.apache.org/licenses/LICENSE-2.0)

from setuptools import setup, find_packages


def version():
    with open('CHANGES') as changes:
        return changes.readline().split(',')[0]


def license():
    with open('LICENSE') as license_type:
        return license_type.readline()


def readme():
    changes_title = '\n\nVersion history\n----------------\n\n'

    with open('README.md') as r:
        with open('CHANGES') as ch:
            return r.read() + changes_title + ch.read()


setup(name='robotframework_grid_downloader_plugin',
      version=version(),
      description='Grid File Downloader plugin for RobotFramework SeleniumLibrary',
      long_description=readme(),
      long_description_content_type="text/markdown",
      url='https://github.com/robco/robotframework-selenium-downloader-plugin',
      author='Robert Malovec',
      author_email='github@malovec.sk',
      license=license(),
      python_requires=">=3.9",
      classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Apache-2.0",
        "Operating System :: OS Independent",
      ],
      packages=find_packages(),
      package_data={},
      install_requires=[
          'robotframework>=7.0.1',
          'robotframework-seleniumlibrary>=6.5.0',
          'requests',
          'certifi'
      ]
)
