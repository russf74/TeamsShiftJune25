import json
import os

def get_config_path():
    return os.path.join(os.path.dirname(__file__), 'config.json')

def load_config():
    path = get_config_path()
    if not os.path.exists(path):
        # Default config
        config = {
            "scan_interval_seconds": 600,
            "gmail_user": "",
            "gmail_app_password": "",
            "alert_email": ""
        }
        with open(path, 'w') as f:
            json.dump(config, f, indent=2)
        return config
    with open(path, 'r') as f:
        return json.load(f)

def save_config(config):
    with open(get_config_path(), 'w') as f:
        json.dump(config, f, indent=2)
