import random
from copy import deepcopy
from typing import Dict
from llm_pretest.prompts.tal_prompt import get_examples as tal_examples
from llm_pretest.prompts.SAP_prompt import get_examples as sap_examples
from llm_pretest.prompts.mem_enc_feb_23_simple import get_examples as mem_enc_examples
from llm_pretest.prompts.global_prompt import get_examples as global_examples
from llm_pretest.prompts.stephanies_prompt import get_examples as stephanies_examples

examples_func = {'tal': tal_examples, 'sap': sap_examples, 'mem_enc': mem_enc_examples, 'global': global_examples,
                 "steph": stephanies_examples}


COMPLETION_1 = """You will read sentences and judge how natural they sound.
You will need to judge, on a scale from 1 to 7, how natural/plausible the presented sentence sounds, and explain yourself shortly. 
All presented sentences will be grammatically correct.

Important: you are encouraged to use the whole scale.

The sentence:
SENTENCE

The naturalness score is:"""


COMPLETION_2 = """You will read sentences and judge how natural they sound.
You will need to judge, on a scale from 1 to 7, how natural/plausible the presented sentence sounds, and explain yourself shortly. 
All presented sentences will be grammatically correct.

Important: you are encouraged to use the whole scale.

Here are some examples:

EXAMPLES 

The sentence:
SENTENCE

The plausibility score is:"""


SYSTEM_1 = """You will read sentences and judge how natural they sound.
You will need to judge, on a scale from 1 to 7, how natural/plausible the presented sentence sounds, and explain yourself.
All presented sentences will be grammatically correct.
Begin all your answers with "The naturalness score is"

Important: you are encouraged to use the whole scale."""


SYSTEM_2 = """You will read sentences and judge how natural they sound.
You will need to judge, on a scale from 1 to 7, how natural/plausible the presented sentence sounds, and explain yourself. 
All presented sentences will be grammatically correct.
Begin all your answers with "The naturalness score is"

Important: you are encouraged to use the whole scale.

Here are some examples:

EXAMPLES"""



CHAT_1 = [{"role": "system", "content": SYSTEM_1}]

CHAT_2 = [{"role": "system", "content": SYSTEM_2}]


def get_prompt_completion(examples: str, sentence: str, add_examples: bool = True):

    if add_examples:
        return COMPLETION_2.replace('EXAMPLES', '\n\n'.join(examples)).replace('SENTENCE', sentence)
    else:
        return COMPLETION_1.replace('SENTENCE', sentence)


def get_prompt_chat(examples: str, sentence: str, add_examples: bool = True):

    user_message = {'role': 'user', "content": sentence}

    if not add_examples:
        chat = [{"role": "system", "content": SYSTEM_1}]
    else:
        chat = [{"role": "system", "content": SYSTEM_2.replace('EXAMPLES', '\n\n'.join(examples))}]
    chat.append(user_message)
    return chat


def get_prompt(prompt_type: str, prompt_name: str, example_args: Dict, sentence: str, add_examples: bool = True):

    examples = examples_func[prompt_name](**example_args)
    func_dic = {'completion': get_prompt_completion, 'chat': get_prompt_chat}
    return func_dic[prompt_type](examples, sentence, add_examples)