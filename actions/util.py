import pathlib
import subprocess
import tempfile


QUOTAS = {
    # production dirs
    '/mnt/homework/homework': '/sbin/zfs set userquota@{uid}=15G homework/homework',
    '/mnt/homework/public_html': '/sbin/zfs set userquota@{uid}=3G homework/public_html',
    '/mnt/homework/private_cvmfs': '/sbin/zfs set userquota@{uid}=10G homework/private_cvmfs',
    '/mnt/lfs7/user': '/usr/bin/lfs setquota -g {gid} --block-softlimit 2000000 --block-hardlimit 2250000 /mnt/lfs7',
    '/mnt/ceph1-npx-user': '/usr/bin/setfattr -n ceph.quota.max_files -v 10000000 /mnt/ceph1-npx-user/{uid}; /usr/bin/setfattr -n ceph.quota.max_bytes -v 2250000000000 /mnt/ceph1-npx-user/{uid}',
    # testing dirs
    '/mnt/homework/homework_test': '/sbin/zfs set userquota@{uid}=15G homework/homework_test',
    '/mnt/lfs7/user_test': '/usr/bin/lfs setquota -g {gid} --block-softlimit 2000000 --block-hardlimit 2250000 /mnt/lfs7',
}

INGORE_DIR_ROLES = {
    # production dirs
    '/mnt/homework/homework': {'appAccount'},
    '/mnt/homework/public_html': {'roleAccount', 'appAccount', 'thirdPartyAccount'},
    '/mnt/homework/private_cvmfs': {'roleAccount', 'appAccount', 'thirdPartyAccount'},
    '/mnt/lfs7/user': {'roleAccount', 'appAccount', 'thirdPartyAccount'},
    '/mnt/ceph1-npx-user': {'roleAccount', 'appAccount', 'thirdPartyAccount'},
    # testing dirs
    '/mnt/homework/homework_test': {'appAccount'},
    '/mnt/lfs7/user_test': {'roleAccount', 'appAccount', 'thirdPartyAccount'},
}

ssh_opts = ['-o', 'UserKnownHostsFile=/dev/null', '-o', 'StrictHostKeyChecking=no']


def ssh(host, *args):
    """Run command on remote machine via ssh."""
    cmd = ['ssh'] + ssh_opts + [f'{host}'] + list(args)
    subprocess.check_call(cmd)


def scp_and_run(host, script_data, script_name='create.py'):
    """Transfer a script to a remote machine, run it, then delete it."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        filename = pathlib.Path(tmpdirname) / script_name
        with open(filename, 'w') as f:
            f.write(script_data)
        cmd = ['scp'] + ssh_opts + [filename, f'{host}:/tmp/{script_name}']
        subprocess.check_call(cmd, stderr=subprocess.DEVNULL)

    try:
        ssh(host, 'python', f'/tmp/{script_name}')
    finally:
        ssh(host, 'rm', f'/tmp/{script_name}')


def scp_and_run_sudo(host, script_data, script_name='create.py'):
    """Transfer a script to a remote machine, run it as root, then delete it."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        filename = pathlib.Path(tmpdirname) / script_name
        with open(filename, 'w') as f:
            f.write(script_data)
        cmd = ['scp'] + ssh_opts + [filename, f'{host}:/tmp/{script_name}']
        subprocess.check_call(cmd, stderr=subprocess.DEVNULL)

    try:
        ssh(host, 'sudo', 'python', f'/tmp/{script_name}')
    finally:
        ssh(host, 'rm', f'/tmp/{script_name}')
