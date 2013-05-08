# -*- Mode: Python; test-case-name: feat.test.test_common_connstr -*-
# vi:si:et:sw=4:sts=4:ts=4

from feat.common import connstr
from feat.test import common


class ConnStrTest(common.TestCase):

    def testFTP(self):
        resp = connstr.parse('ftp://fff.sss.ggg')
        self.assertEqual('ftp', resp['protocol'])
        self.assertEqual(None, resp['user'])
        self.assertEqual(None, resp['password'])
        self.assertEqual(None, resp['port'])
        self.assertEqual('fff.sss.ggg', resp['host'])

    def testPostgres(self):
        resp = connstr.parse('postgres://feat:feat@encoder001.fff.sss.ggg')
        self.assertEqual('postgres', resp['protocol'])
        self.assertEqual('feat', resp['user'])
        self.assertEqual('feat', resp['password'])
        self.assertEqual(None, resp['port'])
        self.assertEqual('encoder001.fff.sss.ggg', resp['host'])

    def testSQLite(self):
        resp = connstr.parse('sqlite:///var/log/journal.sqlite3')
        self.assertEqual('sqlite', resp['protocol'])
        self.assertEqual(None, resp['user'])
        self.assertEqual(None, resp['password'])
        self.assertEqual(None, resp['port'])
        self.assertEqual('/var/log/journal.sqlite3', resp['host'])
