import os,sys

print('test')

print(f'pwd: {os.getcwd()}')
print(f'path: {sys.path}')

from krs import token
t = token.get_token()
print(f'token: {t}')

print('done')
