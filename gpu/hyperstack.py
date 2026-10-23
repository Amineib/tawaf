"""Small Hyperstack client for this project's isolated Blender render jobs.

Uses the same credential location as the other local projects. Credentials never
enter job archives, VM user-data, output, or run manifests.
"""
import json
import os
from pathlib import Path
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError

BASE = 'https://infrahub-api.nexgencloud.com/v1'


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def api(method, path, body=None):
    key = os.environ.get('HYPERSTACK_API_KEY') or (Path.home() / '.config/hyperstack/api_key').read_text().strip()
    assert path.startswith('/') and '\n' not in key and '\r' not in key
    req = Request(BASE + path, method=method,
                  data=None if body is None else json.dumps(body).encode(),
                  headers={'api_key': key, 'Content-Type': 'application/json',
                           'Accept': 'application/json', 'User-Agent': 'HyperstackAutomation/0.1'})
    try:
        with build_opener(NoRedirect()).open(req, timeout=45) as response:
            return json.load(response)
    except HTTPError as error:
        raise RuntimeError(f'Hyperstack {method} {path}: HTTP {error.code}') from None


if __name__ == '__main__':
    import sys
    from concurrent.futures import ThreadPoolExecutor
    paths = sys.argv[1:]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for path, result in zip(paths, pool.map(lambda p: api('GET', p), paths)):
            print(json.dumps({'path': path, 'result': result}))
