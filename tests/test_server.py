import json
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from pathlib import Path
from reporadar.server import make_server


class ServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        (cls.root/'demo.py').write_text('def value():\n    return 1\n')
        cls.server = make_server(cls.root, cls.root/'index.sqlite', port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = 'http://127.0.0.1:' + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.tmp.cleanup()

    def request(self, path, data=None, headers=None):
        request = urllib.request.Request(self.base+path, data=data, headers=headers or {})
        return urllib.request.urlopen(request, timeout=5)

    def test_snapshot_search_and_ui(self):
        with self.request('/api/snapshot') as response:
            snapshot = json.load(response)
        self.assertNotIn('root', snapshot)
        self.assertEqual(snapshot['symbols'][0]['name'], 'value')
        with self.request('/api/search?q=value') as response:
            self.assertEqual(json.load(response)[0]['id'], 'demo.py::value')
        with self.request('/') as response:
            self.assertIn(b'RepoRadar', response.read())
            self.assertIn("default-src 'self'", response.headers['Content-Security-Policy'])

    def test_scan_and_compare(self):
        with self.request('/api/scan', b'{}', {'Content-Type':'application/json'}) as response:
            run = json.load(response)['run_id']
        with self.request(f'/api/compare?before=1&run={run}') as response:
            self.assertEqual(json.load(response)['count'], 0)

    def test_cross_origin_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request('/api/scan', b'{}', {'Content-Type':'application/json', 'Origin':'https://evil.example'})
        self.assertEqual(error.exception.code, 403)

    def test_dns_rebinding_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request('/api/snapshot', headers={'Host':'evil.example'})
        self.assertEqual(error.exception.code, 403)

    def test_arbitrary_file_path_not_exposed(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request('/../../etc/passwd')
        self.assertEqual(error.exception.code, 404)

    def test_invalid_parameters(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request('/api/impact?symbol=missing')
        self.assertEqual(error.exception.code, 400)

    def test_scan_requires_json(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request('/api/scan', b'{}')
        self.assertEqual(error.exception.code, 415)
