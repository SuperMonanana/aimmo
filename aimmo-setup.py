import os
import platform
import subprocess
import shlex

from subprocess import PIPE, CalledProcessError


class Result:
    '''
    Blank object used to store the result of a command run by Popen, do not use this
    outside of the setup script.
    '''
    pass


def _cmd(command):
    '''
    :param command: command/subprocess to be run, as a string
    Takes in a command/subprocess, runs it, then returns an object containing all
    output from the process. DO NOT USE outside of the aimmo-setup script, and DO NOT INCLUDE
    in any release build, as this function is able to run bash scripts, will sudo access if
    specified.
    '''
    result = Result()

    p = subprocess.Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
    (stdout, stderr) = p.communicate()

    result.exit_code = p.returncode
    result.stdout = stdout
    result.stderr = stderr
    result.command = command

    if p.returncode != 0:
        print('Error executing command [%s]' % command)
        print('stderr: [%s]' % stderr)
        print('stdout: [%s]' % stdout)
        raise CalledProcessError

    return result


# First we find and store the OS we are currently on, 0 if we didn't figure it out
# Although if you're not using one the options above for development what are you doing with your life.
hostOS = 0
OStypes = {
    "mac": 1,
    "windows": 2,
    "linux": 3
}

if platform.system() == 'Darwin':
    hostOS = OStypes["mac"]
    print('MAC found!')
elif platform.system() == 'Windows':
    hostOS = OStypes["windows"]
    print('WINDOWS found!')
elif platform.system() == 'Linux':
    hostOS = OStypes["linux"]
    print('LINUX found!')

print('---------------------------------------------------------------------------------------------------')
print('| Welcome to aimmo! This script should make your life alil easier, just be kind if it doesnt work |')
print('| You may be asked to enter your password during this setup                                       |')
print('---------------------------------------------------------------------------------------------------')

if hostOS == OStypes["mac"]:
    """
    This executes the sequence of shell commands needed in order to set up aimmo. At present if changes are made
    to the setup process or versions (such as minikube version) changes, then it will need to be updated manually.
    In future it would be nice to have it automatically find the version we need at the time.

    It would also be nice to implement the ability to automate getting the unity package, however this will require
    selenium and a good amount of thought put into it.

    Note needs homebrew pre-installed in order to run, will let the user know if they don't have it.
    """
    try:
        result = _cmd('brew -v')
        print('Homebrew Found...')
        print(result.stdout)

        try:
            print('Installing Yarn...')
            result = _cmd('brew install yarn')

            print('Installing pipenv...')
            result = _cmd('brew install pipenv')

            print('Running "pipenv install"...')
            result = _cmd('pipenv install')

            print('Installing Docker...')
            result = _cmd('brew cask install docker')

            print('Installing Virtualbox...')
            result = _cmd('brew cask install virtualbox')

            print('Setting up frontend dependencies...')
            result = _cmd('cd ./game_frontend | yarn')

            print('Installing minikube...')
            result = _cmd('curl -Lo minikube https://storage.googleapis.com/minikube/releases/v0.25.2/minikube-darwin-amd64')
            result = _cmd('chmod +x minikube')
            result = _cmd('sudo mv minikube /usr/local/bin/')

            print('Installing Kubernetes...')
            result = _cmd('curl -Lo kubectl https://storage.googleapis.com/kubernetes-release/release/v1.9.4/bin/darwin/amd64/kubectl')
            result = _cmd('chmod +x kubectl')
            result = _cmd('sudo mv kubectl /usr/local/bin/')

            print('adding aimmo to /etc/hosts...')
            result = _cmd("sudo sh -c 'echo 192.168.99.100 local.aimmo.codeforlife.education >> /etc/hosts'")

            print('---------------------------------------------------------------------------------------------------')
            print('| You now need to get the unity package from the aimmo-unity repo, place it in aimmo/static/unity |')
            print('| Also, just open up docker to finalize the install for it, then you can run aimmo.               |')
            print('---------------------------------------------------------------------------------------------------')

        except CalledProcessError as e:
            print('A command has return an exit code != 0, so something has gone wrong.')
        except OSError as e:
            print("Tried to execute a command that didn't exist.")
            print(result.stderr)
        except ValueError as e:
            print('Tried to execute a command with invalid arguments')
            print(result.stderr)

    except Exception as e:
        print('Something went wrong :s, check if Homebrew is installed correctly.')
        print("If it's not that, then something went wrong during the script unexpectedly,")
        print("don't be alarmed, you may have to just try the manual setup. Sorry :(")
        print(result.stderr)


elif hostOS == OStypes["windows"]:
    pass
elif hostOS == OStypes["linux"]:
    pass
else:
    print("Could not detect operating system/ it looks like you're using")
    print('something other then windows, mac, or linux. Y u do dis?')
