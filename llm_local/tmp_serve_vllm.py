import os
import subprocess
import tempfile
from pathlib import Path
import logging

from omegaconf import DictConfig, OmegaConf
import hydra
import json

logger = logging.getLogger(__name__)

def build_cli_flags(flag_args, kv_args):
    flags = ["--"+item for item in flag_args]
    kv_args_list = [[f"--{k}", f"{v}"] for k, v in kv_args.items()]
    kwargs = [item for kv_pair in kv_args_list for item in kv_pair]
    return flags + kwargs

class ProgVLLM:
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
        self.model_path = Path(cfg.model_path)
        self.model_path.mkdir(exist_ok=True, parents=True)
        self.tmp_path = Path(self.workspace.name)
        self.envs = os.environ.copy()
        self.envs.update({
                "FLASHINFER_WORKSPACE_BASE": (self.tmp_path/"flashinfer").as_posix(),
                "HUMMING_TMP_DIR": (self.tmp_path/"humming"/"tmp").as_posix(),
                "HUMMING_CACHE_DIR": (self.tmp_path/"humming"/"cache").as_posix(),
                "HF_HOME": cfg.huggingface.home
                })

        self.server_info_path = Path(self.model_path/"server_info.json")
        self.log_file = open(self.model_path/"vllm-output.log", "w", buffering=1)
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

    def cleanup(self):
        self.workspace.cleanup()
        logger.info("Temporary workspace cleaned up")
        self.log_file.close()
        logger.info("log file closed")
        self.server_info["server_ready"]=False
        self.update_server_info()
        logger.info("server state updated to not_ready")


    def update_server_info(self):
        with open(self.server_info_path, "w", encoding="utf-8") as f:
            json.dump(self.server_info, f)

class VLLMServer:
    """Server class for vllm

    Manages the lifecycle for vllm server through subprocess. 

    - .start(): start the server, exit method after the server is ready to use. 
    - .close(): terminate the server process, clean up tmp folder and close file objects.
    - .monitor(): start monitoring state. can receive keyboard interrupt to close.
    - .serve(): a helper method that provide a one stop method

    After server started, the server should be observable through "server_info"

    """

    def __init__(self, cfg):
        # program related attributes
        self.prog = ProgVLLM(cfg)

        # attributes held for the server class
        self.process = None
        

    def start(self, **input_kwargs):
        kwargs = dict(
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=self.prog.envs
                )
        kwargs.update(input_kwargs)
        self.process = subprocess.Popen(self.prog.command, **kwargs)
        logger.info(f"Child process started: pid={self.process.pid}")
        self._monitor_start()


    def _monitor_start(self):
        
        for line in self.process.stdout:
            
            # stdout are first written to the prog-specifi log file
            self.prog.log_file.write(line)

            if self.prog.startup_str in line:
                logger.info("vllm server start up complete.")
                baseUrl=f"http://{self.server_info["hostname"]}:{self.server_info["port"]}/v1"
                logger.info(f"connect to baseUrl: {baseUrl}")
                self.server_info["server_ready"]=True
                self.prog.update_server_info()
                return 0
        

        # If no start up string is detected after stdout is closed,
        # then something is wrong
        self.process.wait()
        if self.process.returncode != 0:
            raise subprocess.CalledProcessError(
                    returncode=self.process.returncode,
                    cmd=self.prog.command
                    )

        raise RuntimeError(
                "Server exited with code 0 before reporting readiness"
                )

    def close(self):

        # terminate the process
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.info("Subprocess did not exit in time; forcing kill")
                self.process.kill()
                self.process.wait()
            finally:
                logger.info("Subprocess exited.")

        # cleanup program specific stuff
        self.prog.cleanup()

    
    def monitor(self):
        try:
            for line in self.process.stdout:
                self.prog.log_file.write(line)
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt caught! Stopping subprocess..")
            raise

        self.process.wait()
        if self.process.returncode != 0:
            raise subprocess.CalledProcessError(
                    returncode=self.process.returncode,
                    cmd=self.prog.command
                    )

    def serve(self):
        try:
            self.start()
            self.monitor()
        except KeyboardInterrupt:
            pass
        finally:
            self.close()


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

class SlurmVLLMServer(VLLMServer):
    """Extended VLLMServer that uses srun
    """

    def __init__(self, cfg, srun_cfg):
        super().__init__(cfg)
        command = ["srun"]
        srun_command = build_cli_flags(srun_cfg.flag_args, srun_cfg.kv_args)
        command.extend(srun_command)
        get_host_command = [
                    "bash", "-c", 'printf "SERVER_HOST=%s\\n" "$(hostname)"; exec "$@"',
                    "bash"
                ]
        command.extend(get_host_command)
        command.extend(self.prog.command)
        self.prog.command = command

    def _monitor_start(self):
        logger.info("running in slurmvllm")
        for line in self.process.stdout:
            self.log_file.write(line)
            
            if "SERVER_HOST" in line:
                server_id = line.strip().split("=")[1]
                logger.info(f"identified hostname: {server_id}")
                self.server_info["hostname"]=server_id
                self.update_server_info()

            if startup_str in line:
                logger.info("vllm server start up complete.")
                baseUrl=f"http://{self.server_info["hostname"]}:{self.server_info["port"]}/v1"
                logger.info(f"connect to baseUrl: {baseUrl}")
                self.server_info["server_ready"]=True
                self.update_server_info()
                return 0

        # If no start up string is detected after stdout is closed,
        # then something is wrong
        self.process.wait()
        if self.process.returncode != 0:
            raise subprocess.CalledProcessError(
                    returncode=self.process.returncode,
                    cmd=self.prog.command
                    )

        raise RuntimeError(
                "Server exited with code 0 before reporting readiness"
                )


@hydra.main(config_path="configs", config_name="server")
def app(cfg):

    server = VLLMServer(cfg.vllm)
    server.serve()

@hydra.main(config_path="configs", config_name="server")
def srun_app(cfg):

    server = SlurmVLLMServer(cfg.vllm, cfg.slurm)
    server.serve()

if __name__ == "__main__":
    srun_app()
