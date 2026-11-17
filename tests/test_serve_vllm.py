import subprocess
import pytest
import json
from llm_local.serve_vllm import VLLMServer
import sys
from omegaconf import OmegaConf
import time

def test_build_command():
    output = VLLMServer.build_command(
            "example/model", 
            ["enforce-eager", "another-arg"],
            {"id": "test", "path": "/tmp/my path"}) 
    answer = ["vllm", "serve", "example/model", 
              "--enforce-eager", "--another-arg", "--id", "test", 
              "--path", "/tmp/my path"]
    assert output == answer

# Testing with a tiny real process to examine launcher without vllm
def test_start_and_close(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOSTNAME", "test-host")

    cfg = OmegaConf.create({
            "model_name": "test/model",
            "flag_args": [],
            "kv_args": {
                "port": 8899,
                "served-model-name": "test-model",
                "max-model-len": 1024,
                },
            "huggingface": {
                "home": str(tmp_path / "hf-cache")
                },
        })

    server = VLLMServer(cfg)
    workspace_path = server.tmp_path
    server.command = [
            sys.executable,
            "-u",
            "-c",
            'import time; print("startup complete"); time.sleep(60)'
            ]

    try:
        server.start()
        assert server.process is not None and server.process.poll() is None

        assert server.server_info["server_ready"] == True
        with open(server.server_info_path, 'r') as f:
            data = json.load(f)
            assert "server_ready" in data and data["server_ready"] == True
    
        assert workspace_path.exists()


        server.close()
        assert server.process.poll() is not None
        assert server.server_info["server_ready"] == False
        with open(server.server_info_path, 'r') as f:
            data = json.load(f)
            assert "server_ready" in data and data["server_ready"] == False
        assert not workspace_path.exists()
        
    finally:
        if server.process is not None:
            if server.process.poll() is None:
                server.process.kill()
            server.process.wait(timeout=5)
            if server.process.stdout is not None:
                server.process.stdout.close()

        server.log_file.close()
        server.workspace.cleanup()

def test_error_before_ready(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOSTNAME", "test-host")

    cfg = OmegaConf.create({
            "model_name": "test/model",
            "flag_args": [],
            "kv_args": {
                "port": 8899,
                "served-model-name": "test-model",
                "max-model-len": 1024,
                },
            "huggingface": {
                "home": str(tmp_path / "hf-cache")
                },
        })

    server = VLLMServer(cfg)
    workspace_path = server.tmp_path
    server.command = [
            sys.executable,
            "-c",
            'raise SystemExit(7)'
            ]

    try:
        with pytest.raises(subprocess.CalledProcessError) as caught:
            server.serve()

        assert caught.value.returncode == 7
        assert workspace_path.exists() is False
        assert server.log_file.closed
        
    finally:
        if server.process is not None:
            if server.process.poll() is None:
                server.process.kill()
            server.process.wait(timeout=5)
            if server.process.stdout is not None:
                server.process.stdout.close()

        server.log_file.close()
        server.workspace.cleanup()

