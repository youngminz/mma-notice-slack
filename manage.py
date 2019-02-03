#!/usr/bin/env python
import sys

from dotenv import find_dotenv, load_dotenv

from django.core.management import execute_from_command_line

load_dotenv(find_dotenv())

if __name__ == "__main__":
    execute_from_command_line(sys.argv)
