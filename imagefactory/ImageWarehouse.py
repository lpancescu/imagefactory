#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2010-2011 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.  A copy of the GNU General Public License is
# also available at http://www.gnu.org/copyleft/gpl.html.

import logging
import pycurl
import httplib2
import uuid
import os

class ImageWarehouse(object):
    
    # Properties
    def url():
        doc = "The url property."
        def fget(self):
            return self._url
        def fset(self, value):
            self._url = value
        def fdel(self):
            del self._url
        return locals()
    url = property(**url())
    
    # Properties end
    
    def __init__(self, url):
        self.log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        
        if (url.endswith('/')):
             self.url = url[0:len(url)-1]
        else:
            self.url = url
    
    
    def create_bucket(self, bucket_url):
        response_headers, response = httplib2.Http().request(bucket_url, "PUT", headers={'content-type':'text/plain'})
        status = int(response_headers["status"])
        if(399 < status < 600):
            # raise RuntimeError("Could not create bucket: %s" % bucket_url)
            self.log.warning("Creating a bucket returned status %s, maybe the bucket already exists?" % (status, ))
    
    def set_metadata_for_id(self, metadata, object_id, bucket):
        object_url = "%s/%s/%s" % (self.url, bucket, object_id)
        self.log.debug("Setting metadata (%s) for %s" % (metadata, object_url))
        http = httplib2.Http()
        for item in metadata:
            response_header, response = http.request("%s/%s" % (object_url, item), "PUT", body=str(metadata[item]), headers={'content-type':'text/plain'})
    
    def metadata_for_id(self, metadata_keys, object_id, bucket):
        object_url = "%s/%s/%s" % (self.url, bucket, object_id)
        self.log.debug("Getting metadata (%s) from %s" % (metadata_keys, object_url))
        metadata = dict()
        http = httplib2.Http()
        for item in metadata_keys:
            response_header, response = http.request("%s/%s" % (object_url, item), "PUT", body=str(metadata[item]), headers={'content-type':'text/plain'})
            metadata.update(item, response)
        return metadata
    
    def store_image(self, image_id, image_file_path, bucket="images", metadata=None):
        self.create_bucket("%s/%s" % (self.url, bucket))
        object_url = "%s/%s/%s" % (self.url, bucket, image_id)
        image_file = open(image_file_path)
        
        # Upload the image itself
        image_size = os.path.getsize(image_file_path)
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, object_url)
        curl.setopt(pycurl.HTTPHEADER, ["User-Agent: Load Tool (PyCURL Load Tool)"])
        curl.setopt(pycurl.PUT, 1)
        curl.setopt(pycurl.INFILE, image_file)
        curl.setopt(pycurl.INFILESIZE, image_size)
        curl.perform()
        curl.close()
        image_file.close()
        meta_data = dict(uuid=str(image_id), object_type="image")
        if(metadata):
            meta_data.update(metadata)
        self.set_metadata_for_id(meta_data, image_id, bucket)        
    
    def create_provider_image(self, image_id, txt=None, bucket="provider_images", metadata=None):
        self.create_bucket("%s/%s" % (self.url, bucket))
        object_url = "%s/%s/%s" % (self.url, bucket, image_id)
        if(not txt):
            if(metadata):
                txt = "This object has the following metadata keys: %s" % (metadata.keys(), )
            else:
                txt = "This object only exists to hold metadata."
        response_headers, response = httplib2.Http().request(object_url, "PUT", body=txt, headers={'content-type':'text/plain'})
        meta_data = dict(uuid=str(image_id), object_type="provider_image")
        if(metadata):
            meta_data.update(metadata)
        self.set_metadata_for_id(meta_data, image_id, bucket)        
    
    def store_template(self, template, template_id=None, bucket="templates", metadata=None):
        self.create_bucket("%s/%s" % (self.url, bucket))
        if(not template_id):
            template_id = uuid.uuid4()
        object_url = "%s/%s/%s" % (self.url, bucket, template_id)
        response_headers, response = httplib2.Http().request(object_url, "PUT", body=template, headers={'content-type':'text/plain'})
        meta_data = dict(uuid=str(template_id), object_type="template")
        if(metadata):
            meta_data.update(metadata)
        self.set_metadata_for_id(meta_data, template_id, bucket)
        return template_id     
    
    def store_icicle(self, icicle, icicle_id=None, bucket="icicles", metadata=None):
        self.create_bucket("%s/%s" % (self.url, bucket))
        if(not icicle_id):
            icicle_id = uuid.uuid4()
        object_url = "%s/%s/%s" % (self.url, bucket, icicle_id)
        response_headers, response = httplib2.Http().request(object_url, "PUT", body=icicle, headers={'content-type':'text/plain'})
        meta_data = dict(uuid=str(icicle_id), object_type="icicle")
        if(metadata):
            meta_data.update(metadata)
        self.set_metadata_for_id(meta_data, icicle_id, bucket)
        return icicle_id 
    
    def template_with_id(self, template_id, bucket="templates"):
        response_headers, response = httplib2.Http().request("%s/%s/%s" % (url, bucket, template_id), "GET", headers={'content-type':'text/plain'})
        return response
    
    def template_for_image_id(self, image_id, bucket="images"):
        response_headers, template_id = httplib2.Http().request("%s/%s/%s/template" % (url, bucket, image_id), "GET", headers={'content-type':'text/plain'})
        return template_id, self.template_with_id(template_id)
    
    def image_with_id(self, image_id, bucket="images", metadata_keys=None):
        response_headers, response = httplib2.Http().request("%s/%s/%s" % (url, bucket, image_id), "GET", headers={'content-type':'text/plain'})
        return response, self.metadata_for_id(metadata_keys, image_id, bucket)
    
