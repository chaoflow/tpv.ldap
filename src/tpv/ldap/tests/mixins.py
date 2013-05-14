import itertools
import os
import shutil
import subprocess
import sys
import time
import traceback

from ldap.ldapobject import LDAPObject


# required environment variables
SLAPD = os.environ.get('SLAPD')  # if not set, quite some tests will be skipped
SLAPADD = os.environ.get('SLAPADD')

# optional environment variables
DEBUG = bool(os.environ.get('DEBUG'))
KEEP_FAILED = bool(os.environ.get('KEEP_FAILED'))
SLAPD_LOGLEVEL = os.environ.get('SLAPD_LOGLEVEL', '0')


class Slapd(object):
    def setUp(self):
        if not SLAPD:
            self.skipTest('Skipped as no SLAPD was provided')
        try:
            self._setUp()
        except Exception, e:
            # XXX: working around nose to get immediate exception
            # output, not collected after all tests are run
            sys.stderr.write("""
======================================================================
Error setting up testcase: %s
----------------------------------------------------------------------
%s
""" % (str(e), traceback.format_exc()))
            self.tearDown()
            raise e

    def _setUp(self):
        """start slapd

        ldap data dir is wiped and a fresh base dn added. In case of
        errors the SLAPD process is supposed to be killed.
        """
        self.basedir = '/'.join(['var', self.id()])
        os.mkdir(self.basedir)

        datadir = '/'.join([self.basedir, 'data'])
        os.mkdir(datadir)

        shutil.copytree('etc/openldap/schema',
                        '/'.join([self.basedir, 'schema']))

        # start ldap server
        self.slapdbin = os.path.abspath(SLAPD)
        self.slapadd = os.path.abspath(SLAPADD)
        self.slapdconf = os.path.abspath("etc/openldap/slapd.conf")
        self.uri = 'ldapi://ldapi'
        self.loglevel = SLAPD_LOGLEVEL

        # enable setting debug per testcase
        if getattr(self, 'DEBUG', None) is None:
            self.DEBUG = DEBUG
        self.debugflags = tuple(itertools.chain.from_iterable(
            iter(('-d', x)) for x in self.loglevel.split(',')
        ))

        if hasattr(self, 'BASE_LDIF'):
            retcode = subprocess.call(
                (self.slapadd,
                 "-l", os.path.abspath(self.BASE_LDIF),
                 "-f", self.slapdconf),
                cwd=self.basedir,
                stdout=subprocess.PIPE if not self.DEBUG else None,
                stderr=subprocess.PIPE if not self.DEBUG else None)

            if retcode != 0:
                raise Error

        self.slapd = subprocess.Popen(
            (self.slapdbin,
             "-f", self.slapdconf,
             "-s", "0",
             "-h", "ldapi://ldapi") + self.debugflags,
            cwd=self.basedir,
            stdout=subprocess.PIPE if not self.DEBUG else None,
            stderr=None)

        bind_dn = getattr(self, 'bind_dn', 'cn=root,o=o')
        bind_pw = getattr(self, 'bind_pw', 'secret')
        self.bind_dn = bind_dn
        self.bind_pw = bind_pw

        self.TESTROOT = os.getcwdu()
        os.chdir(self.basedir)

        # wait for ldap to appear
        waited = 0
        while True:
            try:
                self.ldap = LDAPObject(self.uri)
                self.ldap.bind_s(bind_dn, bind_pw)
            except:
                if waited > 10:
                    self.tearDown()
                    raise
                time.sleep(0.1)
                waited = waited + 1
            else:
                break

        # add base dn and per testcase entries
        if not hasattr(self, 'BASE_LDIF'):
            base = getattr(self, 'BASE',
                           ('o=o', (('o', 'o'),
                                    ('objectClass', 'organization'))))
            self.BASE = base
            self.ldap.add_s(*self.BASE)

        for dn, entry in getattr(self, 'ENTRIES', dict()).items():
            self.ldap.add_s(dn, entry)

    def tearDown(self):
        self.slapd.kill()
        self.slapd.wait()
        successful = sys.exc_info() == (None, None, None)
        os.chdir(self.TESTROOT)
        if successful or not KEEP_FAILED:
            shutil.rmtree(self.basedir)
