#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Robert Malovec (github@malovec.sk)
# Licensed under Apache-2.0 (http://www.apache.org/licenses/LICENSE-2.0)

import os
import shutil


class Utils:
    """
    Unit testing utility class.
    """

    @staticmethod
    def create_directory(directory):
        os.makedirs(directory, exist_ok=True)

    @staticmethod
    def delete_directory(directory):
        try:
            shutil.rmtree(directory)
        except FileNotFoundError:
            pass

    @staticmethod
    def create_file(directory, file_name):
        Utils.create_directory(directory)
        f = open(os.path.join(directory, file_name), "w")
        f.write("test")
        f.close()

    @staticmethod
    def remove_file(filename):
        if os.path.exists(filename):
            os.remove(filename)

