from pathlib import Path
import time
import json
import logging

logger = logging.getLogger(__name__)

class ModelInfo:
    def __init__(self, model_path: Path):
        if (not isinstance(model_path, Path)) and isinstance(model_path, str):
            model_path = Path(model_path)
        else:
            raise TypeError("input model_path must be either str or pathlib.Path.")
        self.model_path = model_path

        # check if server_info exist
        self.server_info_path : Path = self.model_path / "server_info.json"
        if not self.server_info_path.exists():
            raise ValueError(f"Model {self.model_path} does not have server_info.json.")
    
    def get_server_info(self):
        with open(self.server_info_path, "r") as f:
            server_info = json.load(f)
        return server_info

    def wait_util_ready(self, seconds=10):

        print("Waiting for vllm server startup", end="", flush=True)
        while not self.is_server_ready():
            print(".", end="", flush=True)
            time.sleep(seconds)

    def is_server_ready(self):
        # check model readiness
        server_info = self.get_server_info()
        if server_info["server_ready"] == True:
            logger.debug("\nServer is ready.")
            return True
        else:
            return False


