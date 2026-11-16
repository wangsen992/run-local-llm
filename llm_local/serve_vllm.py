import os
import subprocess
import tempfile
from pathlib import Path
import fcntl

from omegaconf import DictConfig, OmegaConf
import hydra

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

    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"{temp_dir}")

        temp_path = Path(temp_dir)

        # set environment variables
        os.environ["FLASHINFER_WORKSPACE_BASE"] = (temp_path/"flashinfer").as_posix()
        os.environ["HUMMING_TMP_DIR"] = (temp_path/"humming"/"tmp").as_posix()
        os.environ["HUMMING_CACHE_DIR"] = (temp_path/"humming"/"cache").as_posix()
        os.environ["HF_HOME"] = cfg.huggingface.home

        # construct command
        command = build_command(cfg.vllm.model_name, cfg.vllm.flag_args, cfg.vllm.kv_args)
        process = subprocess.Popen(
                command,
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
