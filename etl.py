#!/bin/env python3

import json

with open('data/it_en_vocab.json') as file:
    contents = json.loads(file.read())
    
for k in contents:
    if k == "meta":  continue
    contents[k]['translations'] = list(filter(lambda x: x.strip() != '', contents[k]['translations']))
    
with open('data/it_en_vocab_mod', 'w') as file:
    file.write(json.dumps(contents))