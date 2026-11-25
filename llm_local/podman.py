import argparse
import shutil
import subprocess
import os
from pathlib import Path
import logging

from llm_local.pi_agent_base import random_string_gen

logger = logging.getLogger(__name__)

# Goal: provide the podman sandboxing functionality

def parse_path(input_path):
    if isinstance(input_path, str):
        input_path = Path(input_path)
    if not input_path.exists():
        raise FileExistsError(f"{input_path.as_posix()} does not exist")
    return input_path

class Podman:

    def __init__(self):
        if shutil.which("podman-hpc") is not None:
            self.cmd = "podman-hpc"
        elif shutil.which("podman") is not None:
            self.cmd = "podman"
        else:
            raise FileNotFoundError("Neither podman nor podman-hpc exists.")


    def has_image(self, image_name): 
        result = subprocess.run(
                [self.cmd, "run", "--rm", image_name, "ls"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True)
        if result.returncode != 0:
            return False
        else:
            return True

    def build_image(
            self,
            image_name: str="localhost/pi-agent-test:dev", 
            build_dir="./podman/agent",
            containerfile="./podman/agent/Containerfile"
            ):

        build_dir = parse_path(build_dir)
        containerfile = parse_path(containerfile)
        build_cmd = [ 
                     self.cmd, "build",
                     "-f", containerfile,
                     "-t", image_name,
                     build_dir.as_posix()
                     ]
        logger.info(f"build_cmd: {build_cmd}")

        result = subprocess.run(build_cmd)
        if result.returncode != 0:
            raise ValueError("podman image build failed")
        
        if self.cmd == "podman-hpc":
            migrate_cmd = [self.cmd, "migrate", image_name]
            result = subprocess.run(migrate_cmd)

    def run(
            self, 
            image="ubuntu:24.04",
            prog=["/bin/bash"],
            remove=False,
            interactive=False,
            mounts=[".:/workspace:ro"],
            env={},
            **kwargs,
            ):

        command = [self.cmd, "run"]
        if remove:
            command.append("--rm")
        if interactive:
            command.append("-it")
        envs_items = []
        for key, val in env.items():
            envs_items.extend([ "-e", f"{key}={val}"])
        command.extend(envs_items)
        mount_items = []
        for m in mounts:
            mount_items.extend(["-v", m])
        command.extend(mount_items)
        kv_items = []
        for k, v in kwargs.items():
            kv_items.extend([f"--{k}", v])
        command.extend(kv_items)
        command.append(image)
        command.extend(prog)


        result = subprocess.run(
                command)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="hostname")
    parser.add_argument("--port", help="port")
    parser.add_argument("--agent-dir", help="agent_dir", required=True) 
    args = parser.parse_args()

    image_name = "localhost/pi-agent:dev"
    podman = Podman()
    if podman.has_image(image_name):
        print(f"podman has image {image_name}")
    else:
        print(f"podman doesn't have image {image_name}, build it now.")
        podman.build_image(
                image_name=image_name,
                build_dir="./podman/agent",
                containerfile="./podman/agent/Containerfile"
                )

    # run a pi agent to test
    agent_dir = Path(args.agent_dir).resolve()
    assert agent_dir.exists()

    pod_agent_dir = Path("/workspace")
    mounts = [f"{agent_dir.as_posix()}:{pod_agent_dir.as_posix()}"]
    envs ={"PURDUE_RCAC_GENAI_APIKEY": os.environ["PURDUE_RCAC_GENAI_APIKEY"] }
    kv = {}
    prog = [
            "python", "-m", "llm_local.pi_tui",
            "--agent-dir", pod_agent_dir.as_posix()
            ]
    podman.run(
            image=image_name,
            prog=prog,
            remove=True,
            interactive=True,
            mounts=mounts,
            env=envs,
            **kv
            )
    

