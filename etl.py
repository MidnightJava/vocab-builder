#!/bin/env python3

import json

with open('data/it_en_vocab') as file:
    contents = json.loads(file.read())
    
# for k in contents:
#     if k == "meta":  continue
#     val = contents[k][0]
#     contents[k] = {"translations": [val["text"]], "lastCorrect": "", "count":0}
    
# with open('data/it_en_vocab', 'w') as file:
#     file.write(json.dumps(contents))