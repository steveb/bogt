
import yaml


def load_config():
    return {}


def save_config(conf):
    print(yaml.safe_dump(conf, default_flow_style=False))
