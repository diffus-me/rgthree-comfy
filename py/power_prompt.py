import os

import execution_context
from .log import log_node_warn, log_node_info, log_node_success

from .constants import get_category, get_name
from .power_prompt_utils import get_and_strip_loras
from nodes import LoraLoader, CLIPTextEncode
import folder_paths

NODE_NAME = get_name('Power Prompt')


class RgthreePowerPrompt:

  NAME = NODE_NAME
  CATEGORY = get_category()

  @classmethod
  def INPUT_TYPES(cls, context: execution_context.ExecutionContext):  # pylint: disable = invalid-name, missing-function-docstring
    SAVED_PROMPTS_FILES = folder_paths.get_filename_list(context, 'saved_prompts')
    SAVED_PROMPTS_CONTENT = []
    for filename in SAVED_PROMPTS_FILES:
      with open(folder_paths.get_full_path(context, 'saved_prompts', filename), 'r') as f:
        SAVED_PROMPTS_CONTENT.append(f.read())
    return {
      'required': {
        'prompt': ('STRING', {
          'multiline': True
        }),
      },
      'optional': {
        "opt_model": ("MODEL",),
        "opt_clip": ("CLIP",),
        'insert_lora': (['CHOOSE', 'DISABLE LORAS'] +
                        [os.path.splitext(x)[0] for x in folder_paths.get_filename_list(context, 'loras')],),
        'insert_embedding': ([
          'CHOOSE',
        ] + [os.path.splitext(x)[0] for x in folder_paths.get_filename_list(context, 'embeddings')],),
        'insert_saved': ([
          'CHOOSE',
        ] + SAVED_PROMPTS_FILES,),
      },
      'hidden': {
        'values_insert_saved': (['CHOOSE'] + SAVED_PROMPTS_CONTENT,),
        "context": "EXECUTION_CONTEXT"
      }
    }

  RETURN_TYPES = (
    'CONDITIONING',
    'MODEL',
    'CLIP',
    'STRING',
  )
  RETURN_NAMES = (
    'CONDITIONING',
    'MODEL',
    'CLIP',
    'TEXT',
  )
  FUNCTION = 'main'

  def main(self,
           prompt,
           opt_model=None,
           opt_clip=None,
           insert_lora=None,
           insert_embedding=None,
           insert_saved=None,
           values_insert_saved=None,
           context: execution_context.ExecutionContext=None,):
    if insert_lora == 'DISABLE LORAS':
      prompt, loras, skipped, unfound = get_and_strip_loras(context, prompt, log_node=NODE_NAME, silent=True)
      log_node_info(
        NODE_NAME,
        f'Disabling all found loras ({len(loras)}) and stripping lora tags for TEXT output.')
    elif opt_model is not None and opt_clip is not None:
      prompt, loras, skipped, unfound = get_and_strip_loras(context, prompt, log_node=NODE_NAME)
      if len(loras) > 0:
        for lora in loras:
          opt_model, opt_clip = LoraLoader().load_lora(opt_model, opt_clip, lora['lora'],
                                                       lora['strength'], lora['strength'])
          log_node_success(NODE_NAME, f'Loaded "{lora["lora"]}" from prompt')
        log_node_info(NODE_NAME, f'{len(loras)} Loras processed; stripping tags for TEXT output.')
    elif '<lora:' in prompt:
      prompt, loras, skipped, unfound = get_and_strip_loras(context, prompt, log_node=NODE_NAME, silent=True)
      total_loras = len(loras) + len(skipped) + len(unfound)
      if total_loras:
        log_node_warn(
          NODE_NAME, f'Found {len(loras)} lora tags in prompt but model & clip were not supplied!')
        log_node_info(NODE_NAME, 'Loras not processed, keeping for TEXT output.')

    conditioning = None
    if opt_clip is not None:
      conditioning = CLIPTextEncode().encode(opt_clip, prompt)[0]

    return (conditioning, opt_model, opt_clip, prompt)
