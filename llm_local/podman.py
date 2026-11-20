import shutil
import subprocess
import os
from pathlib import Path
import logging

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

if __name__ == "__main__":

    image_name = "localhost/pi-agent:dev"

    ## code to run the containerized agent
    # podman-hpc run -it --rm -v "./preset_servers/genai_pi:/workspace/pi_preset:ro" localhost/pi-agent:dev 

    
    
