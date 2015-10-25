# polar-flow-export
Command line tool for bulk exporting TCX files from [Polar Flow](https://flow.polar.com/)

Requires [Python](https://www.python.org) 2.7 or later and the [python-dateutil](https://pypi.python.org/pypi/python-dateutil) library.

Usage is as follows:

    python polarflowexport.py <username> <password> <start_date> <end_date> <output_dir>

The start_date and end_date parameters are ISO-8601 date strings (i.e.
year-month-day). An example invocation is as follows:

    python polarflowexport.py me@me.com mypassword 2015-08-01 2015-08-30 /tmp/tcxfiles

Licensed under the Apache Software License v2, see: http://www.apache.org/licenses/LICENSE-2.0

This project is not in any way affiliated with Polar or Polar Flow. It is purely a
hobby project created out of a need to export a large quantity of TCX files from 
Polar Flow.
"""
