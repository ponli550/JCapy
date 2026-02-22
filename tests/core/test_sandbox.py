import pytest
import os
from jcapy.core.sandbox import LocalSandbox, get_sandbox

def test_local_sandbox_run_command():
    sandbox = LocalSandbox()
    result = sandbox.run_command("echo 'hello sandbox'")
    assert result == "hello sandbox"

def test_local_sandbox_file_ops(tmp_path):
    sandbox = LocalSandbox()
    local_file = tmp_path / "test.txt"
    local_file.write_text("content")

    sandbox_path = tmp_path / "sandbox_test.txt"

    sandbox.upload_file(str(local_file), str(sandbox_path))
    assert sandbox_path.exists()
    assert sandbox_path.read_text() == "content"

    download_path = tmp_path / "downloaded.txt"
    sandbox.download_file(str(sandbox_path), str(download_path))
    assert download_path.exists()
    assert download_path.read_text() == "content"

def test_get_sandbox():
    sandbox = get_sandbox("local")
    assert isinstance(sandbox, LocalSandbox)

def test_local_sandbox_error():
    sandbox = LocalSandbox()
    with pytest.raises(RuntimeError, match="Command failed"):
        sandbox.run_command("nonexistentcommand")
