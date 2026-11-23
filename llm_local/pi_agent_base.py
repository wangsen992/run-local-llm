import os
import json
import jinja2
from pathlib import Path
import random
import string
import logging
from pi_agent.coding import PiClient
from pi_agent.errors import PiCommandError

from llm_local.model_info import ModelInfo

logger = logging.getLogger(__name__)
file_path = Path(__file__)
template_path = file_path.parent/"templates"
with open(template_path / "models.json.j2", "r") as f:
    template_str = f.read()

def random_string_gen(n=6):

    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters, k=n))

# starting an agent requires bare minimum the pi dir. 
# Reading model info to start pi agent is an additional step 
class PiAgentBase:

    def __init__(self, pi_dir=None, **kwargs):

        if pi_dir is None:
            pi_dir = Path(f"./tmp_agents/pi-{random_string_gen(6)}")
        self.pi_coding_agent_dir: Path = Path(pi_dir)
        self.pi_coding_agent_dir.mkdir(parents=True, exist_ok=True)

        if "model" in kwargs:
            model = kwargs["model"]
            if isinstance(model, ModelInfo):
                self.construct_pi_dir_from_model_info(model)
            else:
                raise TypeError("input model is not an instance of ModelInfo.")

        self._check_connection()

    def _check_connection(self):
        """
        pi_agent.errors.PiCommandError
        """
        envs = os.environ.copy()
        envs["PI_CODING_AGENT_DIR"] = self.pi_coding_agent_dir.as_posix()
        with  PiClient(no_session=True, env=envs) as pi:
            try:
                result = pi.run("hi")
            except PiCommandError:
                logger.error("Pi directory not usable")
                raise 

    def construct_pi_dir_from_model_info(self, model: ModelInfo):
        """construct pi coding agent dir

        depends on the VLLMServer write match
        """

        self.model = model

        environment = jinja2.Environment()
        template = environment.from_string(template_str)
        models_json = template.render(**model.get_server_info())
        with open(self.pi_coding_agent_dir/"models.json", "w") as f:
            f.write(models_json)
