#!/usr/bin/python3
import os
import argparse
import tempfile
import subprocess
import json
import time
import base64

def get_files():
    return [x for x in os.listdir() if not x.startswith('.')]

def run_job(cmd, name=None, env=None):
    if not name:
        name = 'keycloak-rest-services-'+os.path.splitext(os.path.basename(cmd.split()[0]))[0]
    if not env:
        env = {}
    for k in env:
        env[k] = base64.b64encode(env[k].encode('utf-8'))

    # make code tarball
    if os.path.exists('code.tar.gz'):
        os.remove('code.tar.gz')
    subprocess.run(['tar','-zcf','code.tar.gz']+get_files(), check=True)
    subprocess.run(['kubectl', 'create', 'configmap', f'{name}-code',
                    '--from-file=code.tar.gz'], check=True)
    if os.path.exists('code.tar.gz'):
        os.remove('code.tar.gz')

    try:
        with tempfile.NamedTemporaryFile(dir=os.getcwd(), suffix='.yaml') as k8sfile:
            k8sfile.write(f"""
apiVersion: v1
kind: Secret
metadata:
  name: {name}-secret
type: Opaque
data:""".encode('utf-8'))
            for k in env:
                k8sfile.write(b'\n  ')
                k8sfile.write(k.encode('utf-8'))
                k8sfile.write(b': ')
                k8sfile.write(env[k])
            k8sfile.write(f"""
---
apiVersion: batch/v1
kind: Job
metadata:
  name: {name}-job
  labels:
    environment: dev
    app: keycloak
    service: {name}
spec:
  backoffLimit: 0
  activeDeadlineSeconds: 120
  ttlSecondsAfterFinished: 600
  template:
    spec:
      containers:
      - name: {name}
        image: circleci/python:3.8
        command: ["python", "/opt/{cmd}"]
        env:
        - name: PYTHONPATH
          value: /opt""".encode('utf-8'))
            for k in env:
                k8sfile.write(f"""
        - name: {k}
          valueFrom:
            secretKeyRef:
              name: {name}-secret
              key: {k}""".encode('utf-8'))
            k8sfile.write(f"""
        volumeMounts:
          - name: code-vol
            mountPath: /opt
      initContainers:
      - name: init-code
        image: circleci/python:3.8
        command: ["tar", "-C", "/opt", "-zxf", "/mnt/code.tar.gz"]
        volumeMounts:
          - name: code-vol
            mountPath: /opt
          - name: code-src-vol
            mountPath: /mnt
      volumes:
        - name: code-vol
          emptyDir: {{}}
        - name: code-src-vol
          configMap:
            name: {name}-code
      restartPolicy: Never
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {name}-network-policy
spec:
  podSelector:
    matchLabels:
      environment: dev
      app: keycloak
      service: {name}
  policyTypes:
  - Ingress
  - Egress
  egress:
  - ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 443
""".encode('utf-8'))

            k8sfile.flush()
            subprocess.run(['kubectl', 'apply', '-f', k8sfile.name], check=True)
            print('Job started.')

            while True:
                p = subprocess.run(['kubectl', 'get', 'job', f'{name}-job', '-o', 'json'],
                                   capture_output=True, check=True)
                data = json.loads(p.stdout)
                if 'succeeded' in data['status'] and data['status']['succeeded'] == 1:
                    print('Job completed successfully.\n---')
                    break
                elif 'failed' in data['status'] and data['status']['failed'] == 1:
                    print('Job failed:\n---')
                    break

            subprocess.run(['kubectl', 'logs', '-l', f'job-name={name}-job'])
            print('---')
    finally:
        subprocess.run(['kubectl', 'delete', 'networkpolicies', f'{name}-network-policy'])
        subprocess.run(['kubectl', 'delete', 'job', f'{name}-job'])
        subprocess.run(['kubectl', 'delete', 'secret', f'{name}-secret'])
        subprocess.run(['kubectl', 'delete', 'configmap', f'{name}-code'])

def parse_env(instr):
    return {part.split('=',1)[0]: part.split('=',1)[1] for part in instr.split(',') if '=' in part}

def main():
    parser = argparse.ArgumentParser('run a script as a k8s job')
    parser.add_argument('--name', default=None, help='job name')
    parser.add_argument('-e', '--env', default='', help='job env. ex: A=B,C=D')
    parser.add_argument('cmd', help='script to run')
    args = parser.parse_args()
    run_job(args.cmd, name=args.name, env=parse_env(args.env))

if __name__ == '__main__':
    main()
