import os
import socket
import subprocess
import tempfile
import unittest
from typing import Optional
from urllib.request import urlretrieve


def check_internet_connectifity(
    host: str = "8.8.8.8", port: int = 53, timeout: int = 3
):
    """
    https://stackoverflow.com/a/33117579
    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False


def download(
    url_path: str, local_path: Optional[str] = None, filename: Optional[str] = None
) -> str:
    if not local_path and not filename:
        filename = os.path.basename(url_path)
    if not local_path:
        local_path = os.path.join(tempfile.mkdtemp(), filename)

    if os.path.exists(local_path):
        return local_path
    else:
        try:
            os.makedirs(os.path.dirname(local_path))
        except OSError:
            pass
        url = "https://github.com/Josef-Friedrich/test-files/raw/master/{}".format(
            url_path
        )
        urlretrieve(url, local_path)
        return local_path


class TestCase(unittest.TestCase):
    def assertIsExecutable(self, module: str):
        command = "{}.py".format(module.replace("_", "-"))
        usage = "usage: {}".format(command)

        run = subprocess.run([command], encoding="utf-8", stderr=subprocess.PIPE)
        self.assertEqual(run.returncode, 2)
        self.assertTrue(usage in run.stderr)

        run = subprocess.run(
            ["./jfscripts/{}.py".format(module)],
            encoding="utf-8",
            stderr=subprocess.PIPE,
        )
        self.assertEqual(run.returncode, 2)
        self.assertTrue(usage.replace("-", "_") in run.stderr)

        run = subprocess.run([command, "-h"], encoding="utf-8", stdout=subprocess.PIPE)
        self.assertEqual(run.returncode, 0)
        self.assertTrue(usage in run.stdout)

    def assertExists(self, path: str, message: Optional[str] = None):
        self.assertTrue(os.path.exists(path), message)

    def assertExistsNot(self, path: str, message: Optional[str] = None):
        self.assertFalse(os.path.exists(path), message)
