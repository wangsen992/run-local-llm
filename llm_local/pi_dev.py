import os
import subprocess
import json
import jinja2
from pathlib import Path
import random
import string

def random_string_gen(n=6):

    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters, k=n))

if __name__ == "__main__":

    model_path = Path("./debug")
    template_path = Path("./llm_local/templates/")
    pi_dir = Path(f"./test_agents/pi-{random_string_gen(6)}")
    pi_dir.mkdir(parents=True, exist_ok=True)

    with open(model_path / "server_info.json", "r") as f:
        server_info = json.load(f)
    
    with open(template_path / "models.json.j2", "r") as f:
        template_str = f.read()

    environment = jinja2.Environment()
    template = environment.from_string(template_str)
    models_json = template.render(**server_info)
    with open(pi_dir/"models.json", "w") as f:
        f.write(models_json)

    envs = os.environ.copy()
    envs["PI_CODING_AGENT_DIR"] = pi_dir.as_posix()
    result = subprocess.run("pi", env=envs)
