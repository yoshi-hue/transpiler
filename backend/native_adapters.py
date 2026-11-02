"""Native-source validation adapter discovery with explicit not_run outcomes."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
import base64
import os

ADAPTERS = {
    'COBOL': ('cobc', ['--version']),
    'FORTRAN': ('gfortran', ['--version']),
    'Pascal': ('fpc', ['-iV']),
    'BASIC': ('fbc', ['--version']),
}

CONTAINER_ADAPTERS = {
    'COBOL': {'image': 'mini-transpiler-native:ubuntu24', 'compiler': 'cobc', 'version_args': ['--version'],
              'build': 'cobc -x -free -o /tmp/program /tmp/source.cob && /tmp/program', 'suffix': '.cob'},
    'FORTRAN': {'image': 'gcc:14-bookworm', 'compiler': 'gfortran', 'version_args': ['--version'],
                'build': 'gfortran -o /tmp/program /tmp/source.f90 && /tmp/program', 'suffix': '.f90'},
    'Pascal': {'image': 'mini-transpiler-native:ubuntu24', 'compiler': 'fpc', 'version_args': ['-iV'],
               'build': 'fpc -o/tmp/program /tmp/source.pas >/tmp/build.log && /tmp/program', 'suffix': '.pas'},
    'BASIC': {'image': 'primeimages/freebasic', 'compiler': 'fbc', 'version_args': ['--version'],
              # The benchmark fixture uses line numbers and classic LET/IF syntax.
              'build': 'fbc -lang qb -x /tmp/program /tmp/source.bas && /tmp/program', 'suffix': '.bas'},
}


def native_tool_status(language):
    command = ADAPTERS.get(language)
    if not command:
        return {'status': 'not_run', 'reason': f'No native adapter is defined for {language}.'}
    executable, args = command
    path = shutil.which(executable)
    if not path:
        container = CONTAINER_ADAPTERS.get(language)
        if container and shutil.which('docker'):
            image = os.getenv(f'NATIVE_{language.upper()}_IMAGE', container['image'])
            try:
                result = subprocess.run(
                    ['docker', 'run', '--rm', '--network', 'none', image,
                     container['compiler'], *container['version_args']],
                    capture_output=True, text=True, timeout=15, check=False,
                )
                version = (result.stdout or result.stderr).splitlines()[0] if (result.stdout or result.stderr) else ''
                if result.returncode == 0:
                    return {'status': 'available_container', 'executable': container['compiler'],
                            'container': 'docker', 'image': image, 'version': version, 'reason': ''}
            except (OSError, subprocess.TimeoutExpired):
                pass
        return {'status': 'not_run', 'reason': f'{executable} is not installed.', 'executable': executable}
    try:
        result = subprocess.run([path, *args], capture_output=True, text=True, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'status': 'not_run', 'reason': f'Could not query {executable}: {exc}', 'executable': path}
    version = (result.stdout or result.stderr).splitlines()[0] if (result.stdout or result.stderr) else ''
    return {'status': 'available' if result.returncode == 0 else 'not_run', 'executable': path,
            'version': version, 'reason': '' if result.returncode == 0 else 'version command failed'}


def compile_and_run_native(language, source, *, stdin_data=None, timeout=10):
    """Compile and execute one source program, or return a precise not_run reason."""
    status = native_tool_status(language)
    if status.get('status') != 'available':
        if status.get('status') == 'available_container':
            container = CONTAINER_ADAPTERS[language]
            source_b64 = base64.b64encode(source.encode('utf-8')).decode('ascii')
            command = ['docker', 'run', '--rm', '--network', 'none',
                       '--env', f'SOURCE_B64={source_b64}', status['image'], 'bash', '-lc',
                       f'echo "$SOURCE_B64" | base64 -d > /tmp/source{container["suffix"]} && {container["build"]}']
            try:
                run = subprocess.run(command, input=stdin_data, capture_output=True, text=True,
                                     timeout=timeout, check=False)
            except subprocess.TimeoutExpired:
                return {'status': 'runtime_failed', 'reason': 'containerized native execution timed out.'}
            return {'status': 'passed' if run.returncode == 0 else 'runtime_failed',
                    'stdout': run.stdout, 'stderr': run.stderr, 'exit_status': run.returncode,
                    'compiler': status.get('version'), 'container_image': status.get('image')}
        return {'status': 'not_run', 'reason': status.get('reason', 'native tool unavailable.')}
    executable = status['executable']
    suffixes = {'COBOL': '.cob', 'FORTRAN': '.f90', 'Pascal': '.pas', 'BASIC': '.bas'}
    source_name = 'source' + suffixes[language]
    with tempfile.TemporaryDirectory(prefix='mini-transpiler-native-') as directory:
        root = Path(directory)
        source_path = root / source_name
        binary = root / ('program.exe' if __import__('os').name == 'nt' else 'program')
        source_path.write_text(source, encoding='utf-8')
        compile_commands = {
            'COBOL': [executable, '-x', '-o', str(binary), str(source_path)],
            'FORTRAN': [executable, '-o', str(binary), str(source_path)],
            'Pascal': [executable, '-o' + str(binary), str(source_path)],
            'BASIC': [executable, '-x', str(binary), str(source_path)],
        }
        try:
            build = subprocess.run(compile_commands[language], capture_output=True, text=True,
                                   timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            return {'status': 'not_run', 'reason': 'native compilation timed out.'}
        if build.returncode != 0:
            return {'status': 'compile_failed', 'stdout': build.stdout, 'stderr': build.stderr}
        try:
            run = subprocess.run([str(binary)], input=stdin_data, capture_output=True,
                                 text=True, timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            return {'status': 'runtime_failed', 'reason': 'native execution timed out.'}
        return {'status': 'passed' if run.returncode == 0 else 'runtime_failed',
                'stdout': run.stdout, 'stderr': run.stderr, 'exit_status': run.returncode,
                'compiler': status.get('version'), 'executable': executable}
