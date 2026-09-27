"""Run two extracted candidate files in an ephemeral, offline Linux namespace."""
import argparse
import os
from pathlib import Path
import resource
import signal
import subprocess
import tempfile


def limits():
    for kind, value in [(resource.RLIMIT_AS, 1024**3), (resource.RLIMIT_CPU, 90),
                        (resource.RLIMIT_FSIZE, 32 * 1024**2), (resource.RLIMIT_NOFILE, 128),
                        (resource.RLIMIT_NPROC, 128), (resource.RLIMIT_CORE, 0)]:
        resource.setrlimit(kind, (value, value))


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--author-tests', action='store_true')
    args = parser.parse_args()
    runtime = Path('/home/tanima/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu').resolve()
    checks = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix='inventory-code-') as staging:
        for name in ('inventory.py', 'test_inventory.py'):
            (Path(staging) / name).write_bytes((args.candidate / name).read_bytes())
        cmd = ['bwrap', '--unshare-all', '--die-with-parent', '--new-session', '--cap-drop', 'ALL',
               '--clearenv', '--setenv', 'PATH', '/runtime/bin', '--setenv', 'HOME', '/tmp',
               '--setenv', 'PYTHONDONTWRITEBYTECODE', '1', '--setenv', 'PYTHONPATH', '/candidate',
               '--ro-bind', str(runtime), '/runtime', '--ro-bind', '/lib', '/lib',
               '--ro-bind', '/lib64', '/lib64', '--proc', '/proc', '--dev', '/dev',
               '--tmpfs', '/tmp', '--dir', '/dev/shm', '--ro-bind', staging, '/candidate',
               '--ro-bind', str(checks), '/checks', '--chdir', '/tmp', '/runtime/bin/python3.12', '-B']
        cmd += (['-m', 'unittest', 'discover', '-s', '/candidate', '-p', 'test_inventory.py', '-v']
                if args.author_tests else ['/checks/test_contract.py', '-v'])
        # Output is bounded on disk; PID namespace teardown kills orphaned descendants.
        with tempfile.TemporaryFile() as log:
            proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT,
                                    start_new_session=True, preexec_fn=limits, env={})
            try:
                code = proc.wait(timeout=180)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
                code = 124
            log.seek(0)
            print(log.read(32 * 1024**2).decode('utf-8', 'replace'), end='')
            print(f'ISOLATED_RUN_EXIT={code}')
            raise SystemExit(code)


if __name__ == '__main__':
    main()
