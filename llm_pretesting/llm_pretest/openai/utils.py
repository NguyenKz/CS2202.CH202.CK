from collections import defaultdict

MODEL_TYPE_MAPPING = defaultdict(lambda : 'chat')
MODEL_TYPE_MAPPING['gpt-3.5-turbo'] = 'chat'
MODEL_TYPE_MAPPING['gpt-3.5-turbo-0613'] = 'chat'
MODEL_TYPE_MAPPING['gpt-4'] = 'chat'