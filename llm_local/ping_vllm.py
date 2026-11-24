from pathlib import Path
import jinja2
import requests
import logging

logger = logging.getLogger(__file__)

hostname = "nid200261"
port = "8899"

def request_model_info(hostname, port):

    root_url = f"http://{hostname}:{port}/v1"

    try:
        response = requests.get(root_url + "/models")
        model_data = response.json()['data'][0]
        modelid = model_data["id"]
        modelname = model_data["root"]
        contextWindow = model_data["max_model_len"]
        return {
                'hostname': hostname,
                'port': port,
                'modelid': modelid, 
                'modelname': modelname, 
                'contextWindow': contextWindow
                }

    except Exception as e:
        logger.error(e)
        raise requests.exceptions.ConnectionError(f"No model available at {root_url}")


def create_models_json_from_model_info(model_info):
    try:
        file_path = Path(__file__)
        template_path = file_path.parent/"templates"
        with open(template_path / "models.json.j2", "r") as f:
            template_str = f.read()
    except:
        raise FileNotFoundError(f"no template models.json file at {template_path}")

    environment = jinja2.Environment()
    template = environment.from_string(template_str)
    models_json_str = template.render(model_info)
    return models_json_str

def create_models_json_from_host_n_port(hostname, port):
    model_info = request_model_info(hostname, port)
    models_json_str = create_models_json_from_model_info(model_info)
    return models_json_str


if __name__ == "__main__":
    model_info = request_model_info(hostname, port)
    models_json = create_models_json_from_model_info(model_info)
