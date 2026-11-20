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

def build_image(
        image_name: str="localhost/pi-agent-test:dev", 
        build_dir="./podman/agent",
        containerfile="./podman/agent/Containerfile"
        ):

    if not shutil.which("podman-hpc"):
        raise ValueError("podman-hpc is not available in your system")
    logger.info("podman-hpc is available")
    podman_cmd = "podman-hpc"

    
    build_dir = parse_path(build_dir)
    containerfile = parse_path(containerfile)
    build_cmd = [ 
                 podman_cmd, "build",
                 "-f", containerfile,
                 "-t", image_name,
                 build_dir.as_posix()
                 ]
    logger.info(f"build_cmd: {build_cmd}")

    result = subprocess.run(build_cmd)
    if result.returncode != 0:
        raise ValueError("podman image build failed")

    migrate_cmd = [podman_cmd, "migrate", image_name]
    result = subprocess.run(migrate_cmd)

if __name__ == "__main__":

    image_name = "localhost/pi-agent:dev"
    build_image(image_name)

    source_pi_dir = Path("./preset_servers/genai_pi/")
    workspace_dir = Path(f"./test_agents/agent-{random_string_gen(6)}")
    workspace_dir.mkdir(parents=True)
    target_pi_dir = workspace_dir / "pi"
    shutil.copytree(source_pi_dir, target_pi_dir)
    mounts=[f"{workspace_dir.resolve().as_posix()}:/workspace"]
    mount_args = [item for m in mounts for item in ['-v', m]]
    flags = [
            "-it", "--rm",
            "-e", "PURDUE_RCAC_GENAI_APIKEY"
            ]
    prog_cmd =[
            "python", "-m", "llm_local.pi_tui", 
            "--pi_dir", "/workspace/pi"
            ]
    command = [
            "podman-hpc", "run",
            ]

    command.extend(flags)
    command.extend(mount_args)
    command.append(image_name)
    command.extend(prog_cmd)

    subprocess.run(command)
    ## code to run the containerized agent
    # podman-hpc run -it --rm -v "./preset_servers/genai_pi:/workspace/pi_preset:ro" localhost/pi-agent:dev 
