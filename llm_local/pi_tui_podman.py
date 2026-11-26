"""app script to launch pi agent tui with podman as sandbox

`python -m llm_local.pi_tui_podman`

options:
    --host  hostname for inference server from host machine
    --port  port number for inference server from host machine
    --agent-dir     directory used for pi coding agent workspace
    --env           ENV=VAR for each environmental variables to pass
                    into podman

if agent-dir is not provided, a temporary agent dir will be created. If
agent-dir is provided, but does not exist, then it will also be created. If it
does exist, the agent-dir will be mapped and then checked when the pi_tui.py
script is called in the container for validity.
"""

import os
import argparse
from pathlib import Path
from llm_local.podman import Podman
import logging
from llm_local.utils import random_string_gen

logger = logging.getLogger(__name__)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="hostname")
    parser.add_argument("--port", help="port")
    parser.add_argument("--agent-dir", help="agent_dir") 
    parser.add_argument("--env", nargs="+", help="env vars")
    args = parser.parse_args()

    # Image readiness
    image_name = "localhost/pi-agent:dev"

    podman = Podman()
    if podman.has_image(image_name):
        print(f"podman has image {image_name}")
    else:
        print(f"podman doesn't have image {image_name}, build it now.")
        fpath = Path(__file__)
        container_path =fpath.parent.parent / "podman" / "agent"
        podman.build_image(
                image_name=image_name,
                build_dir=container_path,
                containerfile=container_path / "Containerfile"
                )

    # run a pi agent to test
    # here we are only mapping the agent_dir, we don't do checks or creation.
    # That will be handled by the py_agent_base code
    if args.agent_dir is None:
        agent_dir = Path(f"./tmp_agents/pi-{random_string_gen(6)}").resolve()
    else:
        agent_dir = Path(args.agent_dir).resolve()
    if not agent_dir.exists():
        agent_dir.mkdir(parents=True)

    pod_agent_dir = Path("/workspace/agent")
    mounts = [f"{agent_dir.as_posix()}:{pod_agent_dir.as_posix()}"]
    envs = {}
    if args.host is None:
        if "genai" in args.agent_dir:
            envs["PURDUE_RCAC_GENAI_APIKEY"] =  os.environ["PURDUE_RCAC_GENAI_APIKEY"]
    kv = {}
    prog = [
            "python", "-m", "llm_local.pi_tui",
            "--agent-dir", pod_agent_dir.as_posix()
            ]
    if args.host is not None and args.port is not None:
        # forward the inference server location to the pi agent in the
        # container (reachable via the Slurm/host network, no -p needed)
        prog.extend(["--host", args.host, "--port", args.port])
    podman.run(
            image=image_name,
            prog=prog,
            remove=True,
            interactive=True,
            mounts=mounts,
            env=envs,
            **kv
            )
    

