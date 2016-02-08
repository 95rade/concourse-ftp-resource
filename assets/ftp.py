#!/usr/bin/env python

import ftplib
import glob
import json
import logging
import os
import re
import sys
from distutils.version import StrictVersion
from resource import Resource
from urllib.parse import urlparse

import ftputil


class UriSession(ftplib.FTP):
    """Ftputil session to accept a URI as contructor argument."""

    def __init__(self, uri):
        """Setup FTP session using provided URI."""

        ftplib.FTP.__init__(self)
        port = uri.port or 21
        self.connect(uri.hostname, port)
        if uri.username:
            self.login(uri.username, uri.password)
        else:
            self.login()

        self.cwd(uri.path)

class FTPResource(Resource):
    def context(self,
                uri: str,
                regex: str,
                version_key: str = 'version') -> str:
        self.regex = re.compile(regex)
        self.version_key = version_key

        return ftputil.FTPHost(urlparse(uri), session_factory=UriSession)

    def cmd_check(self) -> str:
        versions = self._matching_versions(self.ftp.listdir('.'))

        return self._versions_to_output(versions)

    def cmd_in(self,
               dest_dir: [str],
               version: str) -> str:
        # get matching version from file list
        versions = self._matching_versions(self.ftp.listdir('.'))

        match_version = next(v for v in versions if v[self.version_key] == version)

        file_name = match_version['file']
        dest_file_path = os.path.join(dest_dir[0], file_name)

        self.ftp.download(file_name, dest_file_path)

        return self._version_to_output(match_version)

    def cmd_out(self,
                src_dir: [str],
                file: str) -> str:
        file_glob = file
        src_file_path = glob.glob(os.path.join(src_dir[0], file_glob))[0]
        file_name = src_file_path.split('/')[-1]

        self.ftp.upload(src_file_path, file_name)

        version = self.regex.match(file_name).groupdict()
        return self._version_to_output(version)

    def _versions_to_output(self, versions: [str]):
        """Convert list of k/v dicts into list of `version` output."""
        versions.sort(key=lambda x: StrictVersion(x[self.version_key]))
        output = [{self.version_key: version[self.version_key]} for version in versions]

        return output

    def _matching_versions(self, file_list: [str]):
        """Return dict of matched regex groups for matching elements in file_list."""
        return [m.groupdict() for m in [self.regex.match(f) for f in file_list] if m]


    def _version_to_output(self, version: str):
        """Convert single k/v version dict into `version`/`metadata` output."""

        output = {'version': {self.version_key: version[self.version_key]}}
        if len(version.keys()) > 1:
            output.update({'metadata': [
                {"name": k, "value": v} for k, v in version.items() if not k == self.version_key
            ]})

        return output

FTPResource().run(os.path.basename(__file__), sys.stdin.read(), sys.argv[1:])