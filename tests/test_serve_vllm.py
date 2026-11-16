from llm_local.serve_vllm import build_command

def test_build_command():
    output = build_command(
            "example/model", 
            ["enforce-eager", "another-arg"],
            {"id": "test", "path": "/tmp/my path"}) 
    answer = ["vllm", "serve", "example/model", 
              "--enforce-eager", "--another-arg", "--id", "test", 
              "--path", "/tmp/my path"]
    assert output == answer

