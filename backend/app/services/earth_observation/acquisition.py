"""Bounded official-host downloads. Raw files still require product-specific QA."""
import hashlib
import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse, urljoin
import httpx


class SourceApprovalRequired(RuntimeError):
    def __init__(self, approval_url: str):
        self.approval_url = approval_url
        super().__init__('NASA requires the account owner to review and accept the data-service EULA.')


def _official(url: str):
    parsed = urlparse(url)
    host = parsed.hostname or ''
    if parsed.scheme != 'https' or parsed.username or parsed.password or parsed.port not in (None, 443) or not any(host == suffix or host.endswith('.'+suffix) for suffix in ('nasa.gov', 'nsidc.org', 'usgs.gov')):
        raise ValueError('Download host must be an approved official HTTPS source')


def download_asset(url: str, root: Path, *, client: httpx.Client | None = None,
                   token: str | None = None, max_bytes: int = 64*1024*1024) -> dict:
    _official(url)
    if not 1 <= max_bytes <= 1024*1024*1024:
        raise ValueError('Download byte budget out of bounds')
    if client is None:
        with httpx.Client(timeout=45, follow_redirects=False) as session:
            return download_asset(url, root, client=session, token=token, max_bytes=max_bytes)
    root.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.download-', dir=root)
    try:
        digest = hashlib.sha256()
        size = 0
        with os.fdopen(fd, 'wb') as stream:
            for _ in range(6):
                _official(url)
                with client.stream('GET', url, headers={'Authorization': f'Bearer {token}'} if token else {}, follow_redirects=False) as response:
                    if response.status_code in (301,302,303,307,308):
                        url = urljoin(url, response.headers.get('location', ''))
                        continue
                    if response.status_code == 403:
                        response.read()
                        try:
                            reason = response.json()
                        except ValueError:
                            reason = {}
                        approval = urlparse(reason.get('resolution_url', ''))
                        if reason.get('error_description') == 'EULA Acceptance Failure' and approval.scheme == 'https' and approval.netloc == 'urs.earthdata.nasa.gov' and approval.path == '/approve_app':
                            raise SourceApprovalRequired(reason['resolution_url'])
                    response.raise_for_status()
                    if 'html' in response.headers.get('content-type','').lower():
                        raise ValueError('HTML login/error response is not a data asset')
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > max_bytes:
                            raise ValueError('Download exceeds configured byte budget')
                        if stream.tell() == 0 and chunk.lstrip().lower().startswith((b'<html', b'<!doctype html')):
                            raise ValueError('HTML login/error response is not a data asset')
                        digest.update(chunk)
                        stream.write(chunk)
                    break
            else:
                raise ValueError('Too many download redirects')
            if size == 0:
                raise ValueError('Empty data asset')
            stream.flush()
            os.fsync(stream.fileno())
        checksum = digest.hexdigest()
        target = root / checksum
        if target.exists() and (target.is_symlink() or hashlib.sha256(target.read_bytes()).hexdigest() != checksum):
            raise ValueError('Existing asset checksum mismatch')
        os.replace(temporary, target)
        return {'checksum_sha256': checksum, 'bytes': size, 'relative_path': checksum,
                'state': 'downloaded_pending_product_qa'}
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
