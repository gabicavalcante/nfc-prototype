#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This simple client uses standard Python modules
along with the Python lxml toolkit from

http://lxml.de/ 

to demonstrate how a SAML ECP client works.

Studying this client is not an acceptable replacement
for reading the ECP profile [ECP] available at

http://docs.oasis-open.org/security/saml/Post2.0/saml-ecp/v2.0/cs01/saml-ecp-v2.0-cs01.pdf

Please read the profile document and consult this script
as one example of a non-conformant client.
This script cannot be considered a conformant client as defined
in section 3.1.3 of [ECP] because it does not support the use of
channel bindings of type "tls-server-end-point" nor does it support
TLS Client Authentication.

This client has been tested on Debian Jessie against
the Shibboleth IdP version 2.4.4 and 3.2.1 and the Shibboleth Native SP 
version 2.5.6.

The script assumes both the IdP and SP are properly configured for ECP
using basic authentication. See the Shibboleth documentation for details.
 
"""

def install_and_import(package):
    import importlib
    success = 0
    try:
        importlib.import_module(package)
    except ImportError:
        import pip
        success = pip.main(['install', package])
    finally:
        if(success != 0):
            print('There are no module named as ' + package)
            return
        globals()[package] = importlib.import_module(package)

import os
import sys
from sys import platform as _platform
import stat

# TODO: organizar configuração de ambiente
if ('Anaconda' in sys.version):
    install_and_import('urllib.request')
    install_and_import('http.cookiejar')
    import urllib.request as urllib2
    import http.cookiejar as cookielib
else:
    install_and_import('cookielib')
    install_and_import('urllib2')

import re
import getpass
import base64

install_and_import('lxml')

from optparse import OptionParser
from lxml import etree
from copy import deepcopy 

SP_ENDPOINTS = {
 "sp" : "sp",
}

class MyCookieJar(cookielib.MozillaCookieJar):
    """
    Custom cookie jar subclassed from Mozilla because the file format
    stored is not useable by the libcurl libraries. See the comment below.
    """
    def save(self, filename=None, ignore_discard=False, ignore_expires=False):
        if filename is None:
            if self.filename is not None: filename = self.filename
            else: raise ValueError(MISSING_FILENAME_TEXT)

        f = open(filename, "w")
        try:
            f.write(self.header)
            now = time.time()
            for cookie in self:
                if not ignore_discard and cookie.discard:
                    continue
                if not ignore_expires and cookie.is_expired(now):
                    continue
                if cookie.secure: secure = "TRUE"
                else: secure = "FALSE"
                if cookie.domain.startswith("."): initial_dot = "TRUE"
                else: initial_dot = "FALSE"
                if cookie.expires is not None:
                    expires = str(cookie.expires)
                else:
                    # change so that if a cookie does not have an expiration
                    # date set it is saved with a '0' in that field instead
                    # of a blank space so that the curl libraries can
                    # read in and use the cookie
                    #expires = ""
                    expires = "0"
                if cookie.value is None:
                    # cookies.txt regards 'Set-Cookie: foo' as a cookie
                    # with no name, whereas cookielib regards it as a
                    # cookie with no value.
                    name = ""
                    value = cookie.name
                else:
                    name = cookie.name
                    value = cookie.value
                f.write(
                    "\t".join([cookie.domain, initial_dot, cookie.path,
                               secure, expires, name, value])+
                    "\n")
        finally:
            f.close()

def get(sp_target, debug=False):
    """
    Given an IdP endpoint for ECP, the desired target
    from the SP, and a login to use against the IdP
    manage an ECP exchange with the SP and the IdP
    and print the contents of the target to stdout
    after establishing a session with the SP.
    """

    # create a cookie jar and cookie handler
    cookie_jar = cookielib.LWPCookieJar()
    cookie_handler = urllib2.HTTPCookieProcessor(cookie_jar)

    # need an instance of HTTPS handler to do HTTPS
    httpsHandler = urllib2.HTTPSHandler(debuglevel = 0)
    if debug:
        httpsHandler.set_http_debuglevel(1)

    # create the base opener object
    opener = urllib2.build_opener(cookie_handler, httpsHandler)

    # headers needed to indicate to the SP an ECP request
    headers = {
                'Accept' : 'text/html; application/vnd.paos+xml',
                'PAOS'   : 'ver="urn:liberty:paos:2003-08";"urn:oasis:names:tc:SAML:2.0:profiles:SSO:ecp"'
                }

    # request target from SP 
    request = urllib2.Request(url=sp_target,headers=headers)

    try:
        response = opener.open(request) 
    except Exception as e:
        print >>sys.stderr, "First request to SP failed: %s" % e
        sys.exit(1)

    # convert the SP resonse from string to etree Element object
    sp_response = etree.XML(response.read())
    if debug: 
        print()
        print("###### BEGIN SP RESPONSE")
        print()
        print(etree.tostring(sp_response))
        print()
        print("###### END SP RESPONSE")
        print()
        
    return sp_response

def saml_request(debug=False):
    sp_tag = "sp2"
    sp_endpoint = SP_ENDPOINTS[sp_tag]
    return get(sp_endpoint, debug) 

if __name__ == "__main__":
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)

    parser.add_option("-d", "--debug", 
                      action="store_true", dest="debug", default=False,
                      help="write debug output to stdout")

    (options, args) = parser.parse_args()

    saml_request(options.debug)
