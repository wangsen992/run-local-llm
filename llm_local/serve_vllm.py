import os
import subprocess
import tempfile
from pathlib import Path
import fcntl
import logging

from omegaconf import DictConfig, OmegaConf
import hydra

logger = logging.getLogger(__name__)

class VLLMServer:

    def __init__(self, cfg):
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

    def run(self, **input_kwargs):
        kwargs = dict(
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=self.envs
                )
        kwargs.update(input_kwargs)
        self.process = subprocess.Popen(self.command, **kwargs)

    
    def monitor(self):
        try:
            for line in self.process.stdout:
                print(line, end="")
            returncode = self.process.wait()
            return returncode
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt caught! Stopping subprocess..")
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print("Subprocess did not exit in time; forcing kill")
                self.process.kill()
                self.process.wait()
        finally:
            print("Cleanup complete")

    def cleanup(self):
        self.workspace.cleanup()
        print("Temporary workspace clean up complete.")

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
    server.run()
    returncode = server.monitor()
    server.cleanup()
    print("End of Script")

if __name__ == "__main__":
    main()
