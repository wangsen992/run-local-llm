import os
import subprocess
import tempfile
from pathlib import Path
import logging

from omegaconf import DictConfig, OmegaConf
import hydra
import json

from llm_local.utils import build_cli_flags
from llm_local.prog import Prog, ProgVLLM
from llm_local.launcher import Launcher

logger = logging.getLogger(__name__)

@hydra.main(config_path="configs", config_name="server")
def app(cfg):

    # construct the program, with hydra configs
    prog = ProgVLLM(cfg.vllm)

    # construct the launcher for the program
    server = Launcher(prog)
    server.serve()

if __name__ == "__main__":
    app()
