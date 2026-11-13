import os
import subprocess
import tempfile
from pathlib import Path
import fcntl

from omegaconf import DictConfig, OmegaConf
import hydra

@hydra.main(config_path="configs", config_name="server")
def main(cfg):

    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"{temp_dir}")

        temp_path = Path(temp_dir)

        # set environment variables
        os.environ["FLASHINFER_WORKSPACE_BASE"] = (temp_path/"flashinfer").as_posix()
        os.environ["HUMMING_TMP_DIR"] = (temp_path/"humming"/"tmp").as_posix()
        os.environ["HUMMING_CACHE_DIR"] = (temp_path/"humming"/"cache").as_posix()
        os.environ["HF_HOME"] = cfg.huggingface.home

        vllm_model_flag_args_str = " ".join(["--"+item for item in cfg.vllm.flag_args])
        vllm_model_kv_args_str = " ".join([f"--{k} {v}" for k, v in cfg.vllm.kv_args.items()])

        # construct command
        command = f"vllm serve {cfg.vllm.model_name} {vllm_model_flag_args_str} {vllm_model_kv_args_str}"
        print(command)
        process = subprocess.Popen(
                command.split(" "),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
                )

        for line in process.stdout:
            print(line, end="")

        process.wait()

    print("End of Script")

if __name__ == "__main__":
    main()

