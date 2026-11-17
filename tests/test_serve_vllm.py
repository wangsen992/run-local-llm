from llm_local.serve_vllm import VLLMServer

def test_build_command():
    output = VLLMServer.build_command(
            "example/model", 
            ["enforce-eager", "another-arg"],
            {"id": "test", "path": "/tmp/my path"}) 
    answer = ["vllm", "serve", "example/model", 
              "--enforce-eager", "--another-arg", "--id", "test", 
              "--path", "/tmp/my path"]
    assert output == answer

