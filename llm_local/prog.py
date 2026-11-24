import os
import subprocess
import tempfile
from pathlib import Path
import logging

from omegaconf import DictConfig, OmegaConf
import json

from llm_local.utils import build_cli_flags

logger = logging.getLogger(__name__)

class Prog:
    """

    Must have prog attributes and methods:
    - .command
    - .envs
    - .log_file
    - .is_startup_complete(line)
    - .set_startup_complete()
    - .cleanup()
    """

    def __init__(self):
        self.command = ""
        self.startup_str = ""

        self.envs = os.environ.copy()

class ProgVLLM(Prog):
    """class that provides helper class for running vllm
    """
    def __init__(self, cfg: OmegaConf):
        self.cfg = cfg

        # program related attributes
        # mandatory attributes
        self.command = self.build_command(cfg.model_name, cfg.flag_args, cfg.kv_args)
        self.startup_str = "startup complete"

        # program specific attributes
        self.workspace = tempfile.TemporaryDirectory()
        self.__tmp_path = Path(self.workspace.name)
        self.envs = os.environ.copy()
        self.envs.update({
                "FLASHINFER_WORKSPACE_BASE": (self.__tmp_path/"flashinfer").as_posix(),
                "HUMMING_TMP_DIR": (self.__tmp_path/"humming"/"tmp").as_posix(),
                "HUMMING_CACHE_DIR": (self.__tmp_path/"humming"/"cache").as_posix(),
                "HF_HOME": cfg.huggingface.home
                })

        self.__model_path = Path(cfg.model_path)
        self.__model_path.mkdir(exist_ok=True, parents=True)
        self.__server_info_path = Path(self.__model_path/"server_info.json")
        self.log_file = open(self.__model_path/"vllm-output.log", "w", buffering=1)
        self.server_info = {
                "hostname": self.envs["HOSTNAME"],
                "port": self.cfg.kv_args.port,
                "modelid": self.cfg.kv_args["served-model-name"],
                "modelname": self.cfg["model_name"],
                "contextWindow": self.cfg.kv_args["max-model-len"],
                "server_ready": False
                }

        # setup methods to run
        self.update_server_info()

    def is_startup_complete(self, line: str) -> bool:
        return self.startup_str in line

    def set_startup_complete(self):
        self.server_info["server_ready"] = True
        self.update_server_info()

    def startup_complete_message(self):
        hostname = self.server_info["hostname"]
        port = self.server_info["port"]
        return f"vllm server hosting now at http://{hostname}:{port}"

    def cleanup(self):
        self.workspace.cleanup()
        logger.info("Temporary workspace cleaned up")
        self.log_file.close()
        logger.info("log file closed")
        self.server_info["server_ready"]=False
        self.update_server_info()
        logger.info("server state updated to not_ready")


    def update_server_info(self):
        with open(self.__server_info_path, "w", encoding="utf-8") as f:
            json.dump(self.server_info, f)

    @staticmethod
    def build_command(
            model,
            flag_args,
            kv_args
            ):

        command = ["vllm", "serve", model]
        flags = build_cli_flags(flag_args, kv_args)
        command.extend(flags)
        return command
    
