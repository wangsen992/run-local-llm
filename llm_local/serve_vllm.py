import os
import subprocess
import tempfile
from pathlib import Path
import fcntl
import logging

from omegaconf import DictConfig, OmegaConf
import hydra
import json

logger = logging.getLogger(__name__)

startup_str = "startup complete"

class VLLMServer:
    """Server class for vllm

    Manages the lifecycle for vllm server through subprocess. 

    - .start(): start the server, exit method after the server is ready to use. 
    - .close(): terminate the server process, clean up tmp folder and close file objects.
    - .monitor(): start monitoring state. can receive keyboard interrupt to close.

    After server started, the server should be observable through "server_info"

    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.command = self.build_command(cfg.model_name, cfg.flag_args, cfg.kv_args)
        self.workspace = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.workspace.name)
        self.envs = os.environ.copy()
        self.envs.update({
                "FLASHINFER_WORKSPACE_BASE": (self.tmp_path/"flashinfer").as_posix(),
                "HUMMING_TMP_DIR": (self.tmp_path/"humming"/"tmp").as_posix(),
                "HUMMING_CACHE_DIR": (self.tmp_path/"humming"/"cache").as_posix(),
                "HF_HOME": cfg.huggingface.home
                })
        self.process = None
        self.log_file = open("./vllm-output.log", "w", buffering=1)
        self.server_info_path = Path("./server_info.json")
        self.server_info = {
                "hostname": self.envs["HOSTNAME"],
                "port": self.cfg.kv_args.port,
                "model-id": self.cfg.kv_args["served-model-name"],
                "model-name": self.cfg["model_name"],
                "contextWindow": self.cfg.kv_args["max-model-len"],
                "server_ready": False
                }
        self.update_server_info()
        
    def update_server_info(self):
        with open(self.server_info_path, "w", encoding="utf-8") as f:
            json.dump(self.server_info, f)

    def start(self, **input_kwargs):
        kwargs = dict(
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=self.envs
                )
        kwargs.update(input_kwargs)
        self.process = subprocess.Popen(self.command, **kwargs)
        logger.info(f"Child process started: pid={self.process.pid}")
        for line in self.process.stdout:
            self.log_file.write(line)

            if startup_str in line:
                logger.info("vllm server start up complete.")
                baseUrl=f"http://{self.server_info["hostname"]}:{self.server_info["port"]}/v1"
                logger.info(f"connect to baseUrl: {baseUrl}")
                self.server_info["server_ready"]=True
                self.update_server_info()
                break

    def close(self):
        self.server_info["server_ready"]=False
        self.update_server_info()
        self.process.terminate()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            logger.info("Subprocess did not exit in time; forcing kill")
            self.process.kill()
            self.process.wait()
        finally:
            logger.info("Subprocess exited.")

        self.workspace.cleanup()
        logger.info("Temporary workspace cleaned up")
        self.log_file.close()
        logger.info("log file closed")
    
    def monitor(self):
        try:
            for line in self.process.stdout:
                self.log_file.write(line)
        except KeyboardInterrupt:
            logger.info("\nKeyboardInterrupt caught! Stopping subprocess..")
            self.close()

        self.process.wait()
        if self.process.returncode != 0:
            raise subprocess.CalledProcessError(f"vllm process exited abnormally. check log for detail. ")

    @staticmethod
    def build_command(
            model,
            flag_args,
            kv_args
            ):

        command = ["vllm", "serve", model]
        flags = ["--"+item for item in flag_args]
        kv_args_list = [[f"--{k}", f"{v}"] for k, v in kv_args.items()]
        kwargs = [item for kv_pair in kv_args_list for item in kv_pair]
        command.extend(flags)
        command.extend(kwargs)
        return command


@hydra.main(config_path="configs", config_name="server")
def main(cfg):

    server = VLLMServer(cfg.vllm)
    server.start()

    server.monitor()

    server.close()
    logger.info("End of Script")

if __name__ == "__main__":
    main()
