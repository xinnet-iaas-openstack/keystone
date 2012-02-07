# Copyright (c) 2011 OpenStack, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import json
from lxml import etree

from keystone import config
from keystone import utils
from keystone.contrib.extensions import CONFIG_EXTENSION_PROPERTY
from keystone.contrib.extensions import DEFAULT_EXTENSIONS
from keystone.logic.types.extension import Extensions

EXTENSIONS_PATH = 'contrib/extensions'
CONF = config.CONF


def get_supported_extensions():
    """
    Returns list of supported extensions.
    """
    extensions = CONF[CONFIG_EXTENSION_PROPERTY] or DEFAULT_EXTENSIONS
    return [extension.strip() for extension in extensions]


def is_extension_supported(extension_name):
    """
    Return True if the extension is enabled, False otherwise.
    extension_name - extension name
    extension_name is case-sensitive.
    """
    if extension_name is not None:
        return extension_name in get_supported_extensions()
    return False


class ExtensionsReader(object):
    """Reader to read static extensions content"""
    def __init__(self, extension_prefix):
        self.extensions = None
        self.extension_prefix = extension_prefix
        self.root = None
        self.supported_extensions = None
        self.__init_extensions()

    def __init_extensions(self):
        self.extensions = Extensions(self.__get_json_extensions(),
            self.__get_xml_extensions())

    def __get_json_extensions(self):
        """ Initializes and returns all json static extension content."""
        body = self.__get_all_json_extensions()
        extensionsarray = body["extensions"]["values"]
        for supported_extension in self.__get_supported_extensions():
            thisextensionjson = self.__get_extension_json(
                supported_extension)
            if thisextensionjson is not None:
                extensionsarray.append(thisextensionjson)
        return json.dumps(body)

    def __get_xml_extensions(self):
        """ Initializes and returns all xml static extension content."""
        body = self.__get_all_xml_extensions()
        for supported_extension in self.__get_supported_extensions():
            thisextensionxml = self.__get_extension_xml(supported_extension)
            if thisextensionxml is not None:
                body.append(thisextensionxml)
        return etree.tostring(body)

    def __get_root(self):
        """ Returns application root.Has a local reference for reuse."""
        if self.root is None:
            self.root = utils.get_app_root()
            self.root = os.path.abspath(self.root) + os.sep
        return self.root

    def __get_file(self, resp_file):
        """ Helper get file method."""
        root = self.__get_root()
        filename = os.path.abspath(os.path.join(root, resp_file.strip('/\\')))
        return open(filename).read()

    def __get_all_json_extensions(self):
        """ Gets empty json extensions content to which specific
        extensions are added."""
        resp_file = "%s/%s.json" % (EXTENSIONS_PATH, 'extensions')
        allextensions = self.__get_file(resp_file)
        return json.loads(allextensions)

    def __get_all_xml_extensions(self):
        """ Gets empty xml extensions content
        to which specific extensions are added."""
        resp_file = "%s/%s.xml" % (EXTENSIONS_PATH, 'extensions')
        allextensions = self.__get_file(resp_file)
        return etree.fromstring(allextensions)

    def __get_supported_extensions(self):
        """ Returns list of supported extensions."""
        if self.supported_extensions is None:
            self.supported_extensions = get_supported_extensions()
        return self.supported_extensions

    def __get_extension_json(self, extension_name):
        """Returns specific extension's json content."""
        thisextension = self.__get_extension_file(extension_name, 'json')
        return thisextension if not thisextension\
            else json.loads(thisextension.read())

    def __get_extension_xml(self, extension_name):
        """Returns specific extension's xml content."""
        thisextension = self.__get_extension_file(extension_name, 'xml')
        return thisextension if not thisextension\
            else etree.parse(thisextension).getroot()

    def __get_extension_file(self, extension_name, request_type):
        """Returns specific static extension file."""
        try:
            extension_dir = "%s/%s/%s" % (EXTENSIONS_PATH,
                self.extension_prefix, extension_name)
            extension_dir = os.path.abspath(os.path.join(self.__get_root(),
                extension_dir.strip('/\\')))
            extension_file = open(os.path.join(extension_dir,
                "extension." + request_type))
            return extension_file
        except IOError:
            return None

    def get_extensions(self):
        """Return Extensions result."""
        return self.extensions
