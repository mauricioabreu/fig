"""Include external projects, allowing services to link to a service
defined in an external project.
"""
import logging

import requests
from six.moves.urllib.parse import urlparse
import yaml
from fig.service import ConfigError


log = logging.getLogger(__name__)


def normalize_url(url):
    url = urlparse(url)
    return url if url.scheme else url._replace(scheme='file')


def read_config(content):
    return yaml.safe_load(content)


def get_project_from_file(url):
    # Handle urls in the form file://./some/relative/path
    path = url.netloc + url.path if url.netloc.startswith('.') else url.path
    with open(path, 'r') as fh:
        return read_config(fh.read())


# TODO: caching for remote options
def get_project_from_http(url, config):
    # TODO: error handling of failed requersts
    # TODO: parse username, or does requests handle that?
    return read_config(requests.get(url).text)


def fetch_external_config(url, include_config):
    log.info("Fetching config from %s" % url.geturl())

    if url.scheme in ('http', 'https'):
        return get_project_from_http(url, include_config)

    if url.scheme == 'file':
        return get_project_from_file(url)

    # TODO: git?
    raise ConfigError("Unsupported url scheme \"%s\" for %s." % (
        url.scheme, url))
