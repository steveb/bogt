
import os

import yaml

config_path = os.path.expanduser('~/.config/bogt.conf')


def load_config():
    if not os.path.exists(config_path):
        return {}
    with open(config_path) as f:
        conf = yaml.safe_load(f)
    return conf


def save_config(conf):
    with open(config_path, 'w') as f:
        yaml.safe_dump(conf, f, default_flow_style=False)
