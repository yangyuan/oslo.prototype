# Copyright 2011 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import copy
import os

from oslo_config import cfg

from prototype.api import common
from prototype.api import wsgi


CONF = cfg.CONF

VERSIONS = {
    "v1.0": {
        "id": "v1.0",
        "status": "CURRENT",
        "updated": "2011-01-21T11:33:21Z",
        "links": [
            {
                "rel": "describedby",
                "type": "text/html",
                "href": 'http://docs.openstack.org/',
            },
        ],
        "media-types": [
            {
                "base": "application/json",
                "type": "application/vnd.openstack.compute+json;version=1",
            }
        ],
    },
    "v2.0": {
        "id": "v2.0",
        "status": "EXPERIMENTAL",
        "updated": "2013-07-23T11:33:21Z",
        "links": [
            {
                "rel": "describedby",
                "type": "text/html",
                "href": 'http://docs.openstack.org/',
            },
        ],
        "media-types": [
            {
                "base": "application/json",
                "type": "application/vnd.openstack.compute+json;version=2",
            }
        ],
    }
}

def get_view_builder(req):
    base_url = req.application_url
    return ViewBuilder(base_url)


class ViewBuilder(common.ViewBuilder):

    def __init__(self, base_url):
        """:param base_url: url of the root wsgi application."""
        self.base_url = base_url

    def build_choices(self, VERSIONS, req):
        version_objs = []
        for version in sorted(VERSIONS):
            version = VERSIONS[version]
            version_objs.append({
                "id": version['id'],
                "status": version['status'],
                "links": [
                    {
                        "rel": "self",
                        "href": self.generate_href(version['id'], req.path),
                    },
                ],
                "media-types": version['media-types'],
            })

        return dict(choices=version_objs)

    def build_versions(self, versions):
        version_objs = []
        for version in sorted(versions.keys()):
            version = versions[version]
            version_objs.append({
                "id": version['id'],
                "status": version['status'],
                "updated": version['updated'],
                "links": self._build_links(version),
            })

        return dict(versions=version_objs)

    def build_version(self, version):
        reval = copy.deepcopy(version)
        reval['links'].insert(0, {
            "rel": "self",
            "href": self.base_url.rstrip('/') + '/',
        })
        return dict(version=reval)

    def _build_links(self, version_data):
        """Generate a container of links that refer to the provided version."""
        href = self.generate_href(version_data['id'])

        links = [
            {
                "rel": "self",
                "href": href,
            },
        ]

        return links

    def generate_href(self, version, path=None):
        """Create an url that refers to a specific version_number."""
        prefix = self._update_compute_link_prefix(self.base_url)
        if version.find('v2.0') == 0:
            version_number = 'v2.0'
        else:
            version_number = 'v1.0'

        if path:
            path = path.strip('/')
            return os.path.join(prefix, version_number, path)
        else:
            return os.path.join(prefix, version_number) + '/'

class Versions(wsgi.Resource):
    def __init__(self):
        super(Versions, self).__init__(None)

    def index(self, req, body=None):
        """Return all versions."""
        builder = get_view_builder(req)
        return builder.build_versions(VERSIONS)

    @wsgi.response(300)
    def multi(self, req, body=None):
        """Return multiple choices."""
        builder = get_view_builder(req)
        return builder.build_choices(VERSIONS, req)

    def get_action_args(self, request_environment):
        """Parse dictionary created by routes library."""
        args = {}
        if request_environment['PATH_INFO'] == '/':
            args['action'] = 'index'
        else:
            args['action'] = 'multi'

        return args