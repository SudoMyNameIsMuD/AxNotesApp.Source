from __future__ import annotations

import os
import threading
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path

try:
    import fcntl
except ModuleNotFoundError:  # pragma: no cover - Windows fallback
    fcntl = None

try:
    import msvcrt
except ModuleNotFoundError:  # pragma: no cover - POSIX fallback
    msvcrt = None

_THREAD_LOCKS = defaultdict(threading.RLock)
_THREAD_LOCKS_GUARD = threading.Lock()
_LOCK_COUNTS = defaultdict(int)
_LOCK_COUNTS_GUARD = threading.Lock()


@contextmanager
def file_lock(path: Path):
    path = path.resolve(strict=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _THREAD_LOCKS_GUARD:
        lock = _THREAD_LOCKS[str(path)]
    with lock:
        with _LOCK_COUNTS_GUARD:
            count = _LOCK_COUNTS[str(path)]
            _LOCK_COUNTS[str(path)] = count + 1
            needs_os_lock = count == 0
        if needs_os_lock:
            with open(path, "a+b") as lock_file:
                if os.name == "nt":
                    if msvcrt is None:
                        raise RuntimeError("msvcrt is unavailable on this platform.")
                    lock_file.seek(0)
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    if fcntl is None:
                        raise RuntimeError("fcntl is unavailable on this platform.")
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    if os.name == "nt":
                        lock_file.seek(0)
                        msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        else:
            try:
                yield
            finally:
                pass
        with _LOCK_COUNTS_GUARD:
            remaining = _LOCK_COUNTS[str(path)] - 1
            if remaining == 0:
                del _LOCK_COUNTS[str(path)]
            else:
                _LOCK_COUNTS[str(path)] = remaining


def notebook_lock_path(path: Path) -> Path:
    candidate = path.resolve(strict=False)
    for parent in (candidate, *candidate.parents):
        if (parent / "AxNotes.toml").exists() or (parent / ".AxNotes").exists():
            return parent / ".AxNotes" / ".notebook.lock"
    return candidate.parent / ".AxNotes" / ".notebook.lock"
