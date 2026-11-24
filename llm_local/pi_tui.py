import os
import subprocess
from pathlib import Path
import logging
import argparse

from llm_local.pi_agent_base import PiAgentBase
from llm_local.model_info import ModelInfo


logger = logging.getLogger(__name__)



class PiTuiAgent(PiAgentBase):

    def run_tui(self):
        envs = os.environ.copy()
        envs["PI_CODING_AGENT_DIR"] = self.pi_coding_agent_dir.as_posix()
        result = subprocess.run("pi", cwd=self.workspace_dir, env=envs)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="hostname")
    parser.add_argument("--port", help="port")
    parser.add_argument("--agent-dir", help="agent_dir") 
    args = parser.parse_args()
    pi = PiTuiAgent(
            agent_dir=args.agent_dir,
            hostname=args.host,
            port=args.port)
    pi.run_tui()

