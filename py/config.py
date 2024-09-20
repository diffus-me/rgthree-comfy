import os
import json
import re

import execution_context
import folder_paths

from .utils import get_dict_value, set_dict_value, dict_has_key, load_json_file
from .pyproject import VERSION



def extend_config(default_config, user_config):
  """ Returns a new config dict combining user_config into defined keys for default_config."""
  cfg = {}
  for key, value in default_config.items():
    if key not in user_config:
      cfg[key] = value
    elif isinstance(value, dict):
      cfg[key] = extend_config(value, user_config[key])
    else:
      cfg[key] = user_config[key] if key in user_config else value
  return cfg


def set_rgthree_user_config(user_hash: str, data: dict):
  """ Sets the user configuration."""
  count = 0
  user_config = get_rgthree_user_config(user_hash)
  for key, value in data.items():
    set_dict_value(user_config, key, value)
    count += 1
  if count > 0:
    write_user_config(user_hash, user_config)


def get_rgthree_user_config_file(user_hash):
  user_dir = folder_paths.get_user_directory(user_hash)
  return os.path.join(user_dir, 'rgthree_config.json')


def get_rgthree_default_config():
  """ Gets the default configuration."""
  global DEFAULT_CONFIG
  if DEFAULT_CONFIG is None:
    DEFAULT_CONFIG = load_json_file(DEFAULT_CONFIG_FILE, default={})
  return DEFAULT_CONFIG


def get_rgthree_user_config(user_hash: str = "default"):
  """ Gets the user configuration."""
  user_config = load_json_file(get_rgthree_user_config_file(user_hash), default={})
  return user_config


def write_user_config(user_hash: str, user_config: dict):
  """ Writes the user configuration."""
  with open(get_rgthree_user_config_file(user_hash), 'w+', encoding='UTF-8') as output_file:
    json.dump(user_config, output_file, sort_keys=True, indent=2, separators=(",", ": "))


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_FILE = os.path.join(THIS_DIR, '..', 'rgthree_config.json.default')
USER_CONFIG_FILE = os.path.join(THIS_DIR, '..', 'rgthree_config.json')

DEFAULT_CONFIG = None
# USER_CONFIG = {}
# RGTHREE_CONFIG = {}


def refresh_config(context: execution_context.ExecutionContext):
  """Refreshes the config."""
  user_config = get_rgthree_user_config(user_hash=context.user_hash)

  # Migrate old config options into "features"
  needs_to_write_user_config = False
  if 'patch_recursive_execution' in user_config:
    del user_config['patch_recursive_execution']
    needs_to_write_user_config = True

  if 'features' in user_config and 'patch_recursive_execution' in user_config['features']:
    del user_config['features']['patch_recursive_execution']
    needs_to_write_user_config = True

  if 'show_alerts_for_corrupt_workflows' in user_config:
    if 'features' not in user_config:
      user_config['features'] = {}
    user_config['features']['show_alerts_for_corrupt_workflows'] = user_config[
      'show_alerts_for_corrupt_workflows']
    del user_config['show_alerts_for_corrupt_workflows']
    needs_to_write_user_config = True

  if 'monitor_for_corrupt_links' in user_config:
    if 'features' not in user_config:
      user_config['features'] = {}
    user_config['features']['monitor_for_corrupt_links'] = user_config['monitor_for_corrupt_links']
    del user_config['monitor_for_corrupt_links']
    needs_to_write_user_config = True

  if needs_to_write_user_config is True:
    print('writing new user config.')
    write_user_config(user_hash=context.user_hash, user_config=user_config)

  # RGTHREE_CONFIG = {"version": VERSION} | extend_config(DEFAULT_CONFIG, user_config)
  #
  # if "unreleased" in user_config and "unreleased" not in RGTHREE_CONFIG:
  #   RGTHREE_CONFIG["unreleased"] = user_config["unreleased"]
  #
  # if "debug" in user_config and "debug" not in RGTHREE_CONFIG:
  #   RGTHREE_CONFIG["debug"] = user_config["debug"]

def get_config(context: execution_context.ExecutionContext):
  """Returns the congfig."""
  default_config = get_rgthree_default_config()
  user_config = get_rgthree_user_config(user_hash=context.user_hash)
  return {"version": VERSION} | extend_config(default_config, user_config)


# refresh_config()
