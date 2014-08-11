"""Include external projects, allowing services to link to a service
defined in an external `fig.yml` file.
"""
import logging

from fig.packages import six
import requests
import yaml


log = logging.getLogger(__name__)


# TODO: test case for different types
def fetch_external_config(fetch_request):
    # TODO: format fetch_request
    log.info("Fetching config from %s" % (fetch_request,))

    def read_config(content):
        return yaml.safe_load(content)

    if 'url' in fetch_request:
        # TODO: error handling of failed requersts
        # TODO: parse username, or does requests handle that?
        return read_config(requests.get(fetch_request['url']).text)

    if 'path' in fetch_request:
        # TODO: error handling
        with open(fetch_request['path'], 'r') as fh:
            return read_config(fh.read())

    # TODO: git?
    # TODO: raise config error as fallback

