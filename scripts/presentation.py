#!/usr/bin/env python3
"""Record a continuous controlled desktop take; authentication needs user input."""

import argparse
import json
import os
from pathlib import Path
import signal
import shlex
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
    demo_windows = []
    environment = None
    stages = []
    started = None
    log = (OUTPUT / (name + '.log')).open('w')
    def stage(label):
        stages.append({'stage': label, 'seconds': round(time.monotonic() - started, 3)})
        (OUTPUT / (name + '-status.json')).write_text(json.dumps(stages, indent=2) + '\n')
        print(label, flush=True)
    def clients():
        return [client for client in json.loads(run('hyprctl', '-j', 'clients')) if client['workspace']['id'] == empty]
    def wait_for(predicate, seconds=12):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            value = predicate()
            if value:
                return value
            pause(.1)
        raise ValueError('Presentation UI did not settle')
    def key(name, delay=.3):
        run('wtype', '-k', name)
        pause(delay)
    def type_text(text):
        for index, char in enumerate(text):
            run('wtype', char)
            pause((.13, .19, .11, .24)[index % 4])
    def health():
        return json.loads(run('omarchy-shell', 'shell', 'call', 'omarchy.menu', 'health', '{}'))
    def focus(address):
        run('hyprctl', 'dispatch', f'hl.dsp.focus({{ window = "address:{address}" }})')
    def close(address):
        run('hyprctl', 'dispatch', f'hl.dsp.window.close({{ window = "address:{address}" }})')
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
        run('omarchy', 'theme', 'bg', 'set', str(CURRENT / 'theme/backgrounds/06.png'))
        workspace(empty)
        pause(2)
        if json.loads(run('hyprctl', '-j', 'activeworkspace'))['windows']:
            raise ValueError('Demo workspace is not empty')
        recorder = subprocess.Popen(['gpu-screen-recorder', '-w', monitor['name'], '-s', '2560x1440',
            '-f', '60', '-fm', 'cfr', '-k', 'h264', '-q', 'very_high', '-cursor', 'no',
            '-fallback-cpu-encoding', 'yes', '-o', str(path)], stdout=log, stderr=log)
        pause(1)
        if recorder.poll() is not None:
            raise ValueError('Recorder did not start; see private log')
        started = time.monotonic()
        stage('Opening desktop on wallpaper 06'); pause(2.6)
        stage('Command menu')
        run('omarchy', 'menu', 'summon', 'root')
        wait_for(lambda: health()['opened'] and health()['keyFocus']); pause(.7)
        for delay in (.36, .31, .54, .28, .5):
            key('Down', delay)
        key('Up', .43); key('Down', .6)
        key('Right', .8)
        wait_for(lambda: health()['activeMenu'] != 'root')
        for direction, delay in (('Down', .4), ('Down', .55), ('Up', .65)):
            key(direction, delay)
        key('Left', .8)
        wait_for(lambda: health()['activeMenu'] == 'root')
        stage('Ghostty search and launch')
        type_text('ghostty')
        wait_for(lambda: health()['rows'] > 0); pause(.75)
        key('Down', .25); key('Up', .4); key('Return', .35)
        first = wait_for(lambda: clients()[0] if len(clients()) == 1 else None)
        demo_windows.append(first['address'])
        focus(first['address'])
        helper = ROOT / 'scripts/presentation-terminal.py'
        run('wtype', 'exec python -B ' + shlex.quote(str(helper)) + ' logo'); key('Return', .8)
        wait_for(lambda: any('Cyberpunk // Logo' in client['title'] for client in clients()))
        stage('Logo and component status at normal terminal font size')
        process = subprocess.Popen(['ghostty', '--title=Cyberpunk // Component Status', '-e',
                                    'python', '-B', str(helper), 'status'], stdout=log, stderr=log, start_new_session=True)
        processes.append(process)
        second = wait_for(lambda: next((client for client in clients() if client['address'] != first['address']), None))
        demo_windows.append(second['address'])
        pause(1.1); focus(first['address']); pause(.8); focus(second['address']); pause(.8)
        stage('Interface scheme inversion and window borders')
        run(CLI, 'scheme', 'set', 'inverted'); pause(1)
        focus(first['address']); pause(.8); focus(second['address']); pause(.8)
        run(CLI, 'scheme', 'set', 'default'); pause(.8)
        close(second['address']); pause(.45); close(first['address']); pause(.7)
        wait_for(lambda: not clients())
        stage('Wallpaper carousel 06 through 11')
        picker = subprocess.Popen(['omarchy', 'menu', 'images', '--selected', str(CURRENT / 'theme/backgrounds/06.png'),
                                   '--show-labels', str(CURRENT / 'theme/backgrounds')], stdout=subprocess.PIPE, stderr=log, text=True,
                                   start_new_session=True)
        processes.append(picker)
        pause(1.2)
        for delay in (.65, .85, .6, 1.1, .9):
            key('Right', delay)
        key('Left', .7); key('Right', 1.0)
        key('Return', .6)
        if picker.poll() is None:
            raise ValueError('Wallpaper picker did not complete')
        selection = picker.stdout.read().strip()
        picker.stdout.close()
        selected = Path(selection).resolve()
        if selected.parent != (CURRENT / 'theme/backgrounds').resolve():
            raise ValueError('Picker returned an unexpected wallpaper')
        if selected.name != '11.png':
            raise ValueError('Carousel did not arrive at wallpaper 11')
        run('omarchy', 'theme', 'bg', 'set', str(selected)); pause(1.1)
        stage('One private sample notification')
        run('notify-send', '-u', 'low', '-a', 'Cyberpunk', '-t', '5000', 'Interface online', 'Your desktop. Your component mix.', env=environment)
        pause(5.6)
        stage('Volume and mute OSD')
        # Native OSD payloads illustrate feedback without changing actual audio.
        for icon, value, duration, delay in (('volume', 35, 1600, .45), ('volume', 40, 1600, .35),
             ('volume', 45, 1600, .5), ('volume', 50, 1600, .4), ('volume', 55, 1600, 1.2),
             ('mute', 0, 1800, 1.6), ('volume', 55, 1800, 1.8)):
            run('omarchy-shell', 'osd', 'show', json.dumps({'icon': icon, 'value': value, 'duration': duration}))
            if run('omarchy-shell', 'osd', 'state') != 'open':
                raise ValueError('OSD did not appear')
            pause(delay)
        if not args.rehearse:
            stage('Polkit: user enters incorrect password then correct password')
            polkit = subprocess.Popen(['pkexec', '/usr/bin/true'], stdout=log, stderr=log, start_new_session=True)
            processes.append(polkit)
            deadline = time.monotonic() + 15
            while 'omarchy-polkit' not in run('hyprctl', '-j', 'layers'):
                if polkit.poll() is not None or time.monotonic() > deadline:
                    raise ValueError('No visible Polkit prompt; cached authorization is not a usable demonstration')
                pause(.15)
            if polkit.wait(timeout=150) != 0:
                raise ValueError('Polkit did not succeed; take not accepted')
            pause(1.6)
        stage('Closing desktop on wallpaper 11'); pause(2.8)
        recorder.send_signal(signal.SIGINT)
        recorder.wait(timeout=15)
        recorder = None
        (OUTPUT / (name + '-result.json')).write_text(json.dumps({'completed': True, 'continuous': True,
            'cursor': False, 'authentication': 'polkit-retry' if not args.rehearse else False,
            'resolution': [2560,1440], 'stages': stages}, indent=2) + '\n')
    finally:
        if recorder is not None and recorder.poll() is None:
            recorder.send_signal(signal.SIGINT)
            recorder.wait(timeout=15)
        for process in processes:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=10)
        addresses = {client['address'] for client in json.loads(run('hyprctl', '-j', 'clients'))}
        for address in demo_windows:
            if address in addresses:
                close(address)
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
