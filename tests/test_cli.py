import pytest

from cocbot.cli import main


def test_execute_is_rejected_for_read_only_laboratory_plan():
    with pytest.raises(SystemExit) as excinfo:
        main(["--plan-laboratory-upgrade", "--execute"])

    assert excinfo.value.code == 2
