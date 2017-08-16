#!/usr/bin/env python2

"""
Command line tool for bulk exporting a range of TCX files from Polar Flow.

Usage is as follows:

    python polarflowexport.py <username> <password> <start_date> \
                <end_date> <output_dir>

The start_date and end_date parameters are ISO-8601 date strings (i.e.
year-month-day). An example invocation is as follows:

    python polarflowexport.py me@me.com mypassword 2015-08-01 2015-08-30 \
                        /tmp/tcxfiles

Licensed under the Apache Software License v2, see:
    http://www.apache.org/licenses/LICENSE-2.0
"""

import cookielib
import dateutil.parser
import json
import logging
import os
import sys
import time
import urllib2
import urllib

#------------------------------------------------------------------------------

class ThrottlingHandler(urllib2.BaseHandler):
    """A throttling handler which ensures that requests to a given host
    are always spaced out by at least a certain number of (floating point)
    seconds.
    """

    def __init__(self, throttleSeconds=1.0):
        self._throttleSeconds = throttleSeconds
        self._requestTimeDict = dict()

    def default_open(self, request):
        hostName = request.get_host()
        lastRequestTime = self._requestTimeDict.get(hostName, 0)
        timeSinceLast = time.time() - lastRequestTime
        
        if timeSinceLast < self._throttleSeconds:
            time.sleep(self._throttleSeconds - timeSinceLast)
        self._requestTimeDict[hostName] = time.time()


#------------------------------------------------------------------------------

class TcxFile(object):
    def __init__(self, workout_id, date_str, content):
        self.workout_id = workout_id
        self.date_str = date_str
        self.content = content


#------------------------------------------------------------------------------

class PolarFlowExporter(object):

    def __init__(self, username, password):
        self._username = username
        self._password = password
        self._logger = logging.getLogger(self.__class__.__name__)

        self._url_opener = urllib2.build_opener(
                        ThrottlingHandler(0.5),
                        urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
        self._url_opener.addheaders = [('User-Agent', 
                'https://github.com/gabrielreid/polar-flow-export')]
        self._logged_in = False

    def _execute_request(self, path, post_params=None):

        url = "https://flow.polar.com%s" % path

        self._logger.debug("Requesting '%s'" % url)

        if post_params != None:
            postData = urllib.urlencode(post_params)
        else:
            postData = None

        try:
            response = self._url_opener.open(url, postData)
            data = response.read()
        except Exception, e:
            self._logger.error("Error fetching %s: %s" % (url, e))
            raise Exception(e)
        response.close()
        return data  

    def _login(self):
        self._logger.info("Logging in user %s", self._username)
        self._execute_request('/')  # Start a new session
        self._execute_request('/login', 
            dict(returnUrl='https://flow.polar.com/', 
                    email=self._username, password=self._password))
        self._logged_in = True 
        self._logger.info("Successfully logged in")

    def get_tcx_files(self, from_date_str, to_date_str):
        """Returns an iterator of TcxFile objects.

        @param from_date_str an ISO-8601 date string
        @param to_date_str an ISO-8601 date string
        """
        self._logger.info("Fetching TCX files from %s to %s", from_date_str, 
                                                                to_date_str)
        if not self._logged_in:
            self._login()

        from_date = dateutil.parser.parse(from_date_str)
        to_date = dateutil.parser.parse(to_date_str)

        from_spec = "%s.%s.%s" % (from_date.day, from_date.month, 
                                    from_date.year)

        to_spec = "%s.%s.%s" % (to_date.day, to_date.month, 
                                    to_date.year)

        path = "/training/getCalendarEvents?start=%s&end=%s" % (
                                                        from_spec, to_spec)
        activity_refs = json.loads(self._execute_request(path))


        def get_tcx_file(activity_ref):
            self._logger.info("Retrieving workout %s" 
                                % activity_ref['listItemId'])
            return TcxFile(
                activity_ref['listItemId'],
                activity_ref['datetime'],
                lambda :self._execute_request(
                    "%s/export/tcx/false" % activity_ref['url'])
                )

        return (get_tcx_file(activity_ref) for activity_ref in activity_refs
            if activity_ref['type'] not in ["TRAININGTARGET", "FITNESSDATA"])

#------------------------------------------------------------------------------

if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)
    try:
        (username, password, from_date_str, 
            to_date_str, output_dir) = sys.argv[1:]
    except ValueError:
        sys.stderr.write(("Usage: %s <username> <password> <from_date> "
            "<to_date> <output_dir>\n") % sys.argv[0])
        sys.exit(1)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    exporter = PolarFlowExporter(username, password)
    for tcx_file in exporter.get_tcx_files(from_date_str, to_date_str):
        filename = "%s_%s.tcx" % (
                        tcx_file.date_str.replace(':', '_'),
                        tcx_file.workout_id)
        filepath = os.path.join(output_dir, filename)
        if os.path.exists(filepath):
            logging.info("skipping %s" % filename)
            continue

        content = tcx_file.content()
        output_file = open(filepath, 'wb')
        output_file.write(content)
        output_file.close()
        print "Wrote file %s" % filename

    print "Export complete"

