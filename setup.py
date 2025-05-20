#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="QuestConfig",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "psutil",
        "watchdog",
        "pywin32;platform_system=='Windows'",
    ],
    entry_points={
        "console_scripts": [
            "questconfig=QuestConfig.ui.app:main",
        ],
    },
) 