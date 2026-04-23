"""Setup-only compatibility patches for sandboxed Windows Python runs."""

from __future__ import annotations

import os
import tempfile


def _mkdtemp_with_writable_windows_acl(suffix=None, prefix=None, dir=None):
    """Match tempfile.mkdtemp but avoid 0700 directories on Windows sandboxes."""
    prefix, suffix, dir, output_type = tempfile._sanitize_params(prefix, suffix, dir)
    names = tempfile._get_candidate_names()

    for _ in range(tempfile.TMP_MAX):
        name = next(names)
        file = os.path.join(dir, prefix + name + suffix)
        try:
            os.mkdir(file, 0o777)
        except FileExistsError:
            continue
        return os.path.abspath(file)

    raise FileExistsError("No usable temporary directory name found")


if os.name == "nt":
    tempfile.mkdtemp = _mkdtemp_with_writable_windows_acl
