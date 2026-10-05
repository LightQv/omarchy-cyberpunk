#!/usr/bin/env python3
"""Record a continuous controlled desktop take; authentication needs user input."""

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'showcase/presentation'
HOME = Path.home()
CURRENT = HOME / '.local/state/omarchy/current'
CLI = str(HOME / '.local/bin/cyberpunk')


def run(*args, env=None):
    return subprocess.check_output(args, text=True, env=env, timeout=20).strip()


def workspace(number):
    run('hyprctl', 'dispatch', f'hl.dsp.focus({{ workspace = "{number}" }})')


def pause(seconds):
    time.sleep(seconds)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rehearse', action='store_true', help='Skip authentication; record a private technical rehearsal')
    parser.add_argument('--take', default='', help='Optional filename suffix for another take')
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    run(CLI, 'check')
    if (CURRENT / 'theme.name').read_text().strip() != 'cyberpunk':
        raise ValueError('Select Cyberpunk before recording')
    name = 'rehearsal' if args.rehearse else 'presentation'
    if args.take:
        if not args.take.isalnum():
            raise ValueError('Take suffix must be alphanumeric')
        name += '-' + args.take
    path = OUTPUT / (name + '.mp4')
    if path.exists():
        raise ValueError(f'Take already exists: {path}; archive it before another take')
    monitor = next(entry for entry in json.loads(run('hyprctl', '-j', 'monitors')) if entry['focused'])
    if monitor['specialWorkspace']['id']:
        raise ValueError('Close the special workspace first')
    original_workspace = monitor['activeWorkspace']['id']
    occupied = {item['id'] for item in json.loads(run('hyprctl', '-j', 'workspaces'))}
    empty = next(number for number in range(1, 100) if number not in occupied)
    wallpaper = str((CURRENT / 'background').resolve())
    scheme = run(CLI, 'scheme', 'status').split(': ', 1)[1]
    dnd = run('omarchy-shell', 'notifications', 'dndState')
    result = json.loads(run('omarchy-shell', 'lock', 'status'))
    if result['locked'] or result['requested'] or result['sessionLocked']:
        raise ValueError('Run while unlocked')
    processes, recorder, private_bus, private_shell = [], None, None, None
    environment = None
    stages = []
    started = None
    log = (OUTPUT / (name + '.log')).open('w')
    def stage(label):
        stages.append({'stage': label, 'seconds': round(time.monotonic() - started, 3)})
        (OUTPUT / (name + '-status.json')).write_text(json.dumps(stages, indent=2) + '\n')
        print(label, flush=True)
    def terminal(title, text, auth=False):
        code = 'import time; print(' + repr(text) + ', flush=True); time.sleep(300)'
        command = ['ghostty', '--title=' + title, '--font-size=18', '-e', 'python', '-c', code]
        if auth:
            done = OUTPUT / 'sudo-result.json'
            done.unlink(missing_ok=True)
            body = "printf '\\n  PRIVILEGED ACCESS\\n\\n  Enter one incorrect password, then the correct password.\\n'; "
            body += 'SUDO_ASKPASS="$1" sudo -A -k /usr/bin/true; result=$?; '
            body += 'printf \'{"exit":%s}\\n\' "$result" > "$2"; sleep 1; exit "$result"'
            command = ['ghostty', '--title=Cyberpunk // Privileged Access', '--font-size=18', '-e',
                       'bash', '--noprofile', '--norc', '-c', body, '--',
                       str(HOME / '.local/share/omarchy-cyberpunk/askpass/cyberpunk-askpass'), str(done)]
        process = subprocess.Popen(command, stdout=log, stderr=log, start_new_session=True)
        processes.append(process)
        return process
    try:
        # A private notification server keeps demonstration messages out of real
        # history. No real notification contents are read or replayed.
        private = OUTPUT / (name + '-private')
        private.mkdir(exist_ok=True)
        home = private / 'home'
        current = home / '.local/state/omarchy/current'
        current.mkdir(parents=True, exist_ok=True)
        if not (current / 'theme').exists():
            (current / 'theme').symlink_to(CURRENT / 'theme')
        for label, source in {'Commons': Path('/usr/share/omarchy/shell/Commons'),
                              'Ui': Path('/usr/share/omarchy/shell/Ui'),
                              'Notifications': HOME / '.config/omarchy/plugins/lightqv.cyberpunk-notifications'}.items():
            if not (private / label).exists():
                (private / label).symlink_to(source)
        qml = private / 'shell.qml'
        qml.write_text('import Quickshell\nimport "Notifications" as Demo\nShellRoot { Demo.Service {} }\n')
        config = private / 'bus.conf'
        config.write_text(f'<busconfig><type>session</type><listen>unix:tmpdir={os.environ["XDG_RUNTIME_DIR"]}</listen><auth>EXTERNAL</auth>'
                         '<policy context="default"><allow own="*"/><allow send_destination="*"/><allow receive_sender="*"/></policy></busconfig>')
        private_bus = subprocess.Popen(['dbus-daemon', '--nofork', '--config-file=' + str(config), '--print-address=1'],
                                       stdout=subprocess.PIPE, stderr=log, text=True)
        address = private_bus.stdout.readline().strip()
        if not address:
            raise ValueError('Private notification bus failed')
        environment = dict(os.environ, HOME=str(home), DBUS_SESSION_BUS_ADDRESS=address,
                           OMARCHY_PATH='/usr/share/omarchy', NO_AT_BRIDGE='1', QT_ACCESSIBILITY='0')
        private_shell = subprocess.Popen(['qs', '-p', str(qml)], env=environment, stdout=log, stderr=log)
        run('omarchy-shell', 'notifications', 'setDnd', 'on')
        run(CLI, 'scheme', 'set', 'default')
        run('omarchy', 'theme', 'bg', 'set', str(HOME / '.config/omarchy/themes/cyberpunk/backgrounds/11.png'))
        workspace(empty)
        pause(2)
        if json.loads(run('hyprctl', '-j', 'activeworkspace'))['windows']:
            raise ValueError('Demo workspace is not empty')
        recorder = subprocess.Popen(['gpu-screen-recorder', '-w', monitor['name'], '-s', '1920x1080',
            '-f', '60', '-fm', 'cfr', '-k', 'h264', '-q', 'very_high', '-cursor', 'no',
            '-fallback-cpu-encoding', 'yes', '-o', str(path)], stdout=log, stderr=log)
        pause(1)
        if recorder.poll() is not None:
            raise ValueError('Recorder did not start; see private log')
        started = time.monotonic()
        stage('Opening desktop'); pause(3)
        first = terminal('Cyberpunk // Signal', '\n  CYBERPUNK\n\n  SIGNAL ESTABLISHED\n\n  Native Omarchy foundations.\n  Your component mix.\n')
        pause(2)
        second = terminal('Cyberpunk // Interface', '\n  INTERFACE ONLINE\n\n  RED / TURQUOISE\n\n  Persistent component controls\n  Switchable interface scheme\n')
        pause(2)
        stage('Window borders and inverted scheme')
        run(CLI, 'scheme', 'set', 'inverted'); pause(3)
        run(CLI, 'scheme', 'set', 'default'); pause(2)
        os.killpg(first.pid, signal.SIGTERM); os.killpg(second.pid, signal.SIGTERM); pause(1)
        stage('Command menu')
        run('omarchy', 'menu', 'summon', 'root'); pause(2)
        run('wtype', '-k', 'Down'); pause(.6)
        run('wtype', '-k', 'Down'); pause(.6)
        run('wtype', 'style'); pause(1.5)
        run('omarchy', 'menu', 'close'); pause(.5)
        stage('Applications')
        run('omarchy', 'menu', 'summon', 'apps'); pause(2)
        run('wtype', 'terminal'); pause(1.5)
        run('omarchy', 'menu', 'close'); pause(.5)
        stage('Wallpaper picker')
        picker = subprocess.Popen(['omarchy', 'theme', 'bg-switcher'], stdout=subprocess.PIPE, stderr=log, text=True,
                                  start_new_session=True)
        processes.append(picker)
        pause(2)
        run('wtype', '-k', 'Right'); pause(1.5)
        run('wtype', '-k', 'Return'); pause(2)
        if picker.poll() is None:
            raise ValueError('Wallpaper picker did not complete')
        selection = picker.stdout.read().strip()
        picker.stdout.close()
        selected = Path(selection).resolve()
        if selected.parent != (CURRENT / 'theme/backgrounds').resolve():
            raise ValueError('Picker returned an unexpected wallpaper')
        run('omarchy', 'theme', 'bg', 'set', str(selected)); pause(2)
        stage('Private sample notifications')
        run('notify-send', '-a', 'Cyberpunk', '-t', '4500', 'Signal established', 'Your desktop. Your component mix.', env=environment)
        pause(1)
        run('notify-send', '-a', 'Cyberpunk', '-t', '3500', 'Interface online', 'Native notifications with a Cyberpunk presentation.', env=environment)
        pause(5)
        run('qs', 'ipc', '-p', str(qml), 'call', 'notifications', 'dismissAll', env=environment)
        pause(.6)
        stage('Volume and mute OSD')
        # Native OSD payloads illustrate feedback without changing actual audio.
        for icon, value, duration in (('volume', 35, 2000), ('volume', 65, 2500), ('mute', 0, 2500)):
            run('omarchy-shell', 'osd', 'show', json.dumps({'icon': icon, 'value': value, 'duration': duration}))
            if run('omarchy-shell', 'osd', 'state') != 'open':
                raise ValueError('OSD did not appear')
            pause(1 if value == 35 else 3)
        if not args.rehearse:
            stage('Sudo: user enters incorrect password then correct password')
            terminal('', '', auth=True)
            done = OUTPUT / 'sudo-result.json'
            deadline = time.monotonic() + 150
            while not done.exists():
                if time.monotonic() > deadline:
                    raise ValueError('Sudo participation timed out')
                pause(.2)
            if json.loads(done.read_text())['exit'] != 0:
                raise ValueError('Sudo did not succeed; take not accepted')
            pause(2)
            stage('Polkit: user enters correct password')
            polkit = subprocess.Popen(['pkexec', '/usr/bin/true'], stdout=log, stderr=log, start_new_session=True)
            processes.append(polkit)
            if polkit.wait(timeout=150) != 0:
                raise ValueError('Polkit did not succeed; take not accepted')
            pause(2)
        stage('Closing desktop'); pause(4)
        recorder.send_signal(signal.SIGINT)
        recorder.wait(timeout=15)
        recorder = None
        (OUTPUT / (name + '-result.json')).write_text(json.dumps({'completed': True, 'continuous': True,
            'cursor': False, 'authentication': not args.rehearse, 'stages': stages}, indent=2) + '\n')
    finally:
        if recorder is not None and recorder.poll() is None:
            recorder.send_signal(signal.SIGINT)
            recorder.wait(timeout=15)
        for process in processes:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=10)
        run('omarchy', 'menu', 'close')
        run('omarchy-shell', 'shell', 'hide', 'omarchy.image-picker')
        run('omarchy-shell', 'osd', 'close')
        for process in (private_shell, private_bus):
            if process is not None and process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
        if private_bus is not None:
            private_bus.stdout.close()
        run(CLI, 'scheme', 'set', scheme)
        run('omarchy', 'theme', 'bg', 'set', wallpaper)
        run('omarchy-shell', 'notifications', 'setDnd', dnd)
        workspace(original_workspace)
        log.close()


if __name__ == '__main__':
    main()
