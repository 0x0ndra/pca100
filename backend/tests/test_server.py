import signal
from typing import NoReturn

import pytest

from pca.server import ServerSupervisor


def _unused_start(host: str, port: int) -> NoReturn:
    raise AssertionError("start() should not be called by these tests")


def _make_supervisor() -> ServerSupervisor:
    return ServerSupervisor(port=0, start=_unused_start)


def test_install_sigterm_handler_registers_a_handler() -> None:
    supervisor = _make_supervisor()
    previous = signal.getsignal(signal.SIGTERM)
    try:
        returned_previous = supervisor._install_sigterm_handler()
        assert returned_previous == previous
        assert signal.getsignal(signal.SIGTERM) != previous
    finally:
        signal.signal(signal.SIGTERM, previous)


def test_sigterm_handler_raises_keyboard_interrupt_to_exit_the_serve_loop() -> None:
    """`serve_forever`'s idle loop only exits on `self._shutdown` or KeyboardInterrupt;
    invoking the installed handler directly must trigger the latter, without sending a
    real signal or spawning a subprocess.
    """
    supervisor = _make_supervisor()
    previous = signal.getsignal(signal.SIGTERM)
    try:
        supervisor._install_sigterm_handler()
        handler = signal.getsignal(signal.SIGTERM)
        with pytest.raises(KeyboardInterrupt):
            handler(signal.SIGTERM, None)
    finally:
        signal.signal(signal.SIGTERM, previous)
