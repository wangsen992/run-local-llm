import os
import argparse
from pathlib import Path
from llm_local.podman import Podman

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="hostname")
    parser.add_argument("--port", help="port")
    parser.add_argument("--agent-dir", help="agent_dir", required=True) 
    parser.add_argument("--env", nargs="+", help="env vars")
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
    if "genai" in args.agent_dir:
        envs ={"PURDUE_RCAC_GENAI_APIKEY": os.environ["PURDUE_RCAC_GENAI_APIKEY"] }
    else:
        envs = {}
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
    

