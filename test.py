import os,sys

print('test')

print(f'pwd: {os.getcwd()}')
print(f'path: {sys.path}')

import util
util.foo()

print('done')
