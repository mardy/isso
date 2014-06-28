# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import unittest
import os
import json

from werkzeug.wrappers import Response

from isso import Isso, config, dist
from isso.utils import http

from fixtures import curl, loads, FakeIP, JSONClient
http.curl = curl


class TestVote(unittest.TestCase):

    def setUp(self):
        conf = config.load(os.path.join(dist.location, "isso", "defaults.ini"))
        conf.set("guard", "enabled", "off")
        conf.set("hash", "algorithm", "none")

        self.app = Isso(conf)

    def makeClient(self, ip):
        return JSONClient(FakeIP(self.app.wsgi_app, ip), Response)

    def testZeroLikes(self):

        rv = self.makeClient("127.0.0.1").post("/new?uri=test", data=json.dumps({"text": "..."}))
        self.assertEqual(loads(rv.data)['likes'], 0)
        self.assertEqual(loads(rv.data)['dislikes'], 0)

    def testSingleLike(self):

        self.makeClient("127.0.0.1").post("/new?uri=test", data=json.dumps({"text": "..."}))
        rv = self.makeClient("0.0.0.0").post("/id/1/like")

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(loads(rv.data)["likes"], 1)

    def testSelfLike(self):

        bob = self.makeClient("127.0.0.1")
        bob.post("/new?uri=test", data=json.dumps({"text": "..."}))
        rv = bob.post('/id/1/like')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(loads(rv.data)["likes"], 0)

    def testMultipleLikes(self):

        self.makeClient("127.0.0.1").post("/new?uri=test", data=json.dumps({"text": "..."}))
        for num in range(15):
            rv = self.makeClient("1.2.%i.0" % num).post('/id/1/like')
            self.assertEqual(rv.status_code, 200)
            self.assertEqual(loads(rv.data)["likes"], num + 1)

    def testVoteOnNonexistentComment(self):
        rv = self.makeClient("1.2.3.4").post('/id/1/like')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(loads(rv.data), None)

    def testDislike(self):
        self.makeClient("127.0.0.1").post("/new?uri=test", data=json.dumps({"text": "..."}))
        rv = self.makeClient("1.2.3.4").post('/id/1/dislike')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(loads(rv.data)['likes'], 0)
        self.assertEqual(loads(rv.data)['dislikes'], 1)
