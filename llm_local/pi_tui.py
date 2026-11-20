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
        result = subprocess.run("pi", env=envs)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
            prog="Pi TUI",
            description="Start a TUI session with pi coding agent"
            )
    parser.add_argument("--pi_dir",required=True)
    args = parser.parse_args()

    pi = PiTuiAgent(pi_dir=args.pi_dir) 
    pi.run_tui()

    # model = ModelInfo("./debug/qwen3.8-27b-fp8/")
    # model.wait_util_ready()

    # pi = PiTuiAgent(model)
    # pi.run_tui()

    # logger.info("pi interactive session completed")
    


