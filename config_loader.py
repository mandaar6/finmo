# config_loader.py - loads the config file and returns settings

import os
import yaml


def load_config(config_path="config/config.yaml"):
    """Read config.yaml and return it as a dictionary."""

    if not os.path.exists(config_path):
        print(f"[!] Config file not found: {config_path}")
        print("    Run setup.sh or setup.ps1 first, or copy config.yaml.template to config.yaml")
        return None

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return config
