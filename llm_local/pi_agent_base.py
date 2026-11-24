import os
import json
import jinja2
from pathlib import Path
import random
import string
import logging
from pi_agent.coding import PiClient
from pi_agent.errors import PiCommandError


from llm_local.ping_vllm import create_models_json_from_host_n_port

logger = logging.getLogger(__name__)

def random_string_gen(n=6):

    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters, k=n))

# starting an agent requires bare minimum the pi dir. 
# Reading model info to start pi agent is an additional step 
class PiAgentBase:
    """

    There are three keys things for pi coding agent:
    - its workspace, or working directory
    - PI_CODING_AGENT_DIR, where it stores model configurations, system prompt,
      skills and extensions
    - models.json

    The full agent will be stored in an agent directory. If a name is give, then
    it will use that name, if not, it will be given a random name

    This class takes a directory for agent dir, and a models_json str that will
    be written to the pi_dir. 

    If agent_dir does not exist, a new one will be created. 

    If the agent_dir already exists, we will reuse the agent dir, resume the
    agent, so its history will be recovered.
    """

    def __init__(self, agent_dir=None, overwrite=False, hostname=None, port=None,  **kwargs):

        if agent_dir is None:
            agent_dir = f"./tmp_agents/pi-{random_string_gen(6)}"
        self.agent_dir = Path(agent_dir).resolve()

        # [x] init when agent_dir is not present
        if not self.agent_dir.exists():
            self.agent_dir.mkdir(parents=True)
            self.pi_coding_agent_dir: Path = Path(self.agent_dir/"pi").resolve()
            self.pi_coding_agent_dir.mkdir(parents=True, exist_ok=True)
            self.workspace_dir: Path = Path(self.agent_dir/"workspace").resolve()
            self.workspace_dir.mkdir(parents=True, exist_ok=True)

            # write models.json
            if hostname is None or port is None:
                raise ValueError("hostname and port must be provided")
            models_json_str = create_models_json_from_host_n_port(hostname, port)
            with open(self.pi_coding_agent_dir/"models.json", 'w') as f:
                f.write(models_json_str)

        if self._has_connection():
            logger.info("Pi Agent established good connection")

    def _has_connection(self):
        """
        pi_agent.errors.PiCommandError
        """
        envs = os.environ.copy()
        envs["PI_CODING_AGENT_DIR"] = self.pi_coding_agent_dir.as_posix()
        with PiClient(cwd=self.workspace_dir.as_posix(), no_session=True, env=envs) as pi:
            try:
                result = pi.run("hi this is a test for connection")
                print(result.text.strip())
                return True
            except PiCommandError:
                logger.error("Pi directory not usable")
                return False

if __name__ == "__main__":
    pi_agent = PiAgentBase(
            agent_dir=None,
            hostname="nid200261",
            port=8899)
    # envs = os.environ.copy()
    # # envs["PI_CODING_AGENT_DIR"] = self.pi_coding_agent_dir.as_posix()
    # envs["PI_CODING_AGENT_DIR"] = "./debug_agent/pi/"

    # with PiClient(no_session=True, env=envs) as pi:
    #     result = pi.run("hi")
    #     print(result.text)
    #     breakpoint()
