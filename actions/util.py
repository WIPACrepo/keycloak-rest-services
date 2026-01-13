import pathlib
import subprocess
import tempfile
import time

from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError

QUOTAS = {
    # production dirs
    '/mnt/homework/homework': '/sbin/zfs set userquota@{uid}=15G homework/homework',
    '/mnt/homework/public_html': '/sbin/zfs set userquota@{uid}=3G homework/public_html',
    '/mnt/homework/private_cvmfs': '/sbin/zfs set userquota@{uid}=10G homework/private_cvmfs',
    '/mnt/lfs7/user': '/usr/bin/lfs setquota -g {gid} --block-softlimit 2000000 --block-hardlimit 2250000 /mnt/lfs7',
    '/mnt/ceph1-npx-user': '/usr/bin/setfattr -n ceph.quota.max_files -v 10000000 /mnt/ceph1-npx-user/{username}; /usr/bin/setfattr -n ceph.quota.max_bytes -v 2250000000000 /mnt/ceph1-npx-user/{username}',
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

ssh_opts = [
    '-o', 'UserKnownHostsFile=/dev/null',
    '-o', 'LogLevel=ERROR',
    '-o', 'StrictHostKeyChecking=no',
    '-o', 'HostKeyAlgorithms=+ssh-rsa',
    '-o', 'PubkeyAcceptedAlgorithms=+ssh-rsa',
]


class RetryError(Exception):
    def __init__(self, sleep_time_history, exception_history):
        self.sleep_time_history = sleep_time_history
        self.exception_history = exception_history
        super().__init__()

    def __str__(self):
        return (f"RetryError(sleep_time_history={self.sleep_time_history}, "
                f"exception_history={self.exception_history})")


def group_tree_to_list(root):
    """Convert a Keycloak group dict hierarchy to a list.

    The first element of the list is guaranteed to be the root node.

    Args:
        root (dict): root group dict with subgroups stored as a list under 'subGroups' key
    Returns:
        list of group dicts, with first element being the root node
    """
    result = []

    def convert_node(node):
        # First element of result MUST be the root of the tree
        result.append(node)
        for child in node['subGroups']:
            convert_node(child)

    convert_node(root)
    return result


def retry_execute(request, max_attempts=8):
    """Retry calling request.execute() with exponential backoff.

    Args:
        request: object with .execute() method
        max_attempts: maximum number of re-attempts

    Returns:
        Return value of request.execute()

    Raises:
        RetryError if reached max_attempts
    """
    if not hasattr(request, 'execute'):
        raise AttributeError(f"{type(request)} object has no attribute 'execute'")
    sleep_time_history = []
    exception_history = []
    for attempt in range(max_attempts):
        sleep_time = 2 ** attempt - 1
        time.sleep(sleep_time)
        sleep_time_history.append(sleep_time)
        try:
            return request.execute()
        except RefreshError as exc:
            # Refreshing the credentials' access token failed. This can be transient, so retry.
            exception_history.append(exc)
            continue
        except HttpError as exc:
            exception_history.append(exc)
            if exc.status_code in (400, 404, 412, 500, 503):
                # Something required not ready yet: 400 (bad request), 412 (precondition failed).
                # Possibly transient: 400 (bad request), 404 (not found), 503 (service unavailable),
                # 500 (internal error).
                continue
            else:
                raise RetryError(sleep_time_history, exception_history) from exc
    else:
        raise RetryError(sleep_time_history, exception_history)


def reflow_text(text, para_sep="\n\n", **kwargs):
    """Try to make the message look nice by re-wrapping lines

    Args:
        text (str): Text to re-flow.
        para_sep (str): paragraph separator
        kwargs: kwargs to pass to textwrap.wrap

    Returns:
        Re-wrapped text
    """
    import textwrap
    # .strip() removes possible newlines if paragraphs are separated by too
    # many newlines (which otherwise would be converted to spaces and make
    # everything look weird)
    paragraphs = [para.strip() for para in text.split(para_sep)]
    wrapped_para_list = [textwrap.wrap(para, **kwargs) for para in paragraphs]
    wrapped_paras = ['\n'.join(para) for para in wrapped_para_list]
    return para_sep.join(wrapped_paras)


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
        ssh(host, 'python3', f'/tmp/{script_name}')
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
        ssh(host, 'sudo', 'python3', f'/tmp/{script_name}')
    finally:
        ssh(host, 'rm', f'/tmp/{script_name}')
