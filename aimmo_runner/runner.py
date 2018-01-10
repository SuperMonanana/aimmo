import logging
import os
import subprocess
import sys
import time
from subprocess import CalledProcessError

_ROOT_DIR_LOCATION = os.path.abspath(os.path.dirname((os.path.dirname(__file__))))
_MANAGE_PY = os.path.join(_ROOT_DIR_LOCATION, 'example_project', 'manage.py')
_SERVICE_PY = os.path.join(_ROOT_DIR_LOCATION, 'aimmo-game-creator', 'service.py')


def log(message):
    print >> sys.stderr, message


def run_command(args, capture_output=False):
    try:
        if capture_output:
            return subprocess.check_output(args)
        else:
            subprocess.check_call(args)
    except CalledProcessError as e:
        log('Command failed with exit status %d: %s' % (e.returncode, ' '.join(args)))
        raise


PROCESSES = []


def run_command_async(args):
    p = subprocess.Popen(args)
    PROCESSES.append(p)
    return p


def create_superuser_if_missing(username, password):
    from django.contrib.auth.models import User
    try:
        User.objects.get_by_natural_key(username)
    except User.DoesNotExist:
        log('Creating superuser %s with password %s' % (username, password))
        User.objects.create_superuser(username=username, email='admin@admin.com',
                                      password=password)


def run(use_minikube, server_wait=True):
    logging.basicConfig()
    sys.path.append(os.path.join(_ROOT_DIR_LOCATION, 'example_project'))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "example_project.settings")

    run_command(['pip', 'install', '-e', _ROOT_DIR_LOCATION])
    run_command(['python', _MANAGE_PY, 'migrate', '--noinput'])
    run_command(['python', _MANAGE_PY, 'collectstatic', '--noinput'])

    create_superuser_if_missing(username='admin', password='admin')

    server_args = []
    if use_minikube:
        # Import minikube here, so we can install the deps first
        run_command(['pip', 'install', '-r', os.path.join(_ROOT_DIR_LOCATION,
                                                          'minikube_requirements.txt')])
        from aimmo_runner import minikube

        minikube.start()
        server_args.append('0.0.0.0:8000')
        os.environ['AIMMO_MODE'] = 'minikube'
    else:
        time.sleep(2)
        game = run_command_async(['python', _SERVICE_PY, '127.0.0.1', '5000'])
        os.environ['AIMMO_MODE'] = 'threads'
    server = run_command_async(['python', _MANAGE_PY, 'runserver'] + server_args)

    try:
        game.wait()
    except NameError:
        pass

    if server_wait is True:
        server.wait()

    return PROCESSES
