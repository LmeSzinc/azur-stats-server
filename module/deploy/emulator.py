import asyncio
import os
import re
import subprocess
import winreg
import shutil

from module.deploy.utils import cached_property

asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


class VirtualBoxEmulator:
    UNINSTALL_REG = "SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall"

    def __init__(self, name, root_path, adb_path, vbox_path, vbox_name):
        """
        Args:
            name (str): Emulator name in windows uninstall list.
            root_path (str): Relative path from uninstall.exe to emulator installation folder.
            adb_path (str, list[str]): Relative path to adb.exe. List of str if there are multiple adb in emulator.
            vbox_path (str): Relative path to virtual box folder.
            vbox_name (str): Regular Expression to match the name of .vbox file.
        """
        self.name = name
        self.root_path = root_path
        self.adb_path = adb_path if isinstance(adb_path, list) else [adb_path]
        self.vbox_path = vbox_path
        self.vbox_name = vbox_name

    @cached_property
    def root(self):
        """
        Returns:
            str: Root installation folder of emulator.

        Raises:
            FileNotFoundError: If emulator not installed.
        """
        reg = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, f'{self.UNINSTALL_REG}\\{self.name}', 0)
        res = winreg.QueryValueEx(reg, 'UninstallString')[0]

        file = re.search('"(.*?)"', res)
        file = file.group(1) if file else res
        root = os.path.abspath(os.path.join(os.path.dirname(file), self.root_path))
        return root

    @cached_property
    def adb_binary(self):
        return [os.path.abspath(os.path.join(self.root, a)) for a in self.adb_path]

    @cached_property
    def adb_backup(self):
        return [f'{a}.bak' for a in self.adb_binary]

    @cached_property
    def serial(self):
        """
        Returns:
            list[str]: Such as ['127.0.0.1:62001', '127.0.0.1:62025']
        """
        vbox = []
        for path, folders, files in os.walk(os.path.join(self.root, self.vbox_path)):
            for file in files:
                if re.match(self.vbox_name, file):
                    file = os.path.join(path, file)
                    vbox.append(file)

        serial = []
        for file in vbox:
            with open(file, 'r') as f:
                for line in f.readlines():
                    # <Forwarding name="port2" proto="1" hostip="127.0.0.1" hostport="62026" guestport="5555"/>
                    res = re.search('<*?hostport="(.*?)".*?guestport="5555"/>', line)
                    if res:
                        serial.append(f'127.0.0.1:{res.group(1)}')

        return serial

    def adb_replace(self, adb):
        """
        Backup the adb in emulator folder to xxx.bak, replace it with your adb.
        Need to call `adb kill-server` before replacing.

        Args:
            adb (str): Absolute path to adb.exe
        """
        for ori, bak in zip(self.adb_binary, self.adb_backup):
            if not os.path.exists(bak):
                print(f'Replacing {ori}')
                shutil.move(ori, bak)
                shutil.copy(adb, ori)

    def adb_recover(self):
        """ Revert adb replacement """
        for ori, bak in zip(self.adb_binary, self.adb_backup):
            if os.path.exists(ori):
                os.remove(ori)
            shutil.move(bak, ori)


# NoxPlayer 夜神模拟器
nox_player = VirtualBoxEmulator(
    name="Nox",
    root_path=".",
    adb_path=["./adb.exe", "./nox_adb.exe"],
    vbox_path="./BignoxVMS",
    vbox_name='.*.vbox$'
)
# LDPlayer 雷电模拟器
ld_player = VirtualBoxEmulator(
    name="LDPlayer",
    root_path=".",
    adb_path="./adb.exe",
    vbox_path="./vms",
    vbox_name='.*.vbox$'
)
ld_player_4 = VirtualBoxEmulator(
    name="LDPlayer4",
    root_path=".",
    adb_path="./adb.exe",
    vbox_path="./vms",
    vbox_name='.*.vbox$'
)
# MemuPlayer 逍遥模拟器
memu_player = VirtualBoxEmulator(
    name="MEmu",
    root_path="../",
    adb_path="./adb.exe",
    vbox_path="./MemuHyperv VMs",
    vbox_name='.*.memu$'
)
# MumuPlayer MuMu模拟器
mumu_player = VirtualBoxEmulator(
    name="Nemu",
    root_path=".",
    adb_path="./vmonitor/bin/adb_server.exe",
    vbox_path="./vms",
    vbox_name='.*.nemu$'
)


class EmulatorConnect:
    SUPPORTED_EMULATORS = [nox_player, ld_player, ld_player_4, memu_player, mumu_player]

    def __init__(self, adb='adb.exe'):
        self.adb_binary = adb

    def _execute(self, cmd):
        cmd = [self.adb_binary] + cmd
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate(timeout=10)
        result = stdout.decode()
        return result

    @cached_property
    def emulators(self):
        """
        Returns:
            list: List of installed emulators on current computer.
        """
        emulators = []
        for emulator in self.SUPPORTED_EMULATORS:
            try:
                serial = emulator.serial
                emulators.append(emulator)
            except FileNotFoundError:
                continue
            if len(serial):
                print(f'Emulator {emulator.name} found, instances: {serial}')

        return emulators

    def devices(self):
        """
        Returns:
            list[str]: Connected devices in adb
        """
        result = self._execute(['devices'])
        devices = []
        for line in result.replace('\r\r\n', '\n').replace('\r\n', '\n').split('\n'):
            if line.startswith('List') or '\t' not in line:
                continue
            serial, status = line.split('\t')
            if status == 'device':
                devices.append(serial)

        return devices

    def adb_kill(self):
        self._execute(['devices'])
        self._execute(['kill-server'])

    @cached_property
    def serial(self):
        """
        Returns:
            list[str]: All available emulator serial on current computer.
        """
        serial = []
        for emulator in self.emulators:
            serial += emulator.serial
            for s in emulator.serial:
                ip, port = s.split(':')
                port = int(port) - 1
                if 5554 <= int(port) < 5600:
                    serial.append(f'emulator-{port}')

        return serial

    def brute_force_connect(self):
        """ Brute-force connect all available emulator instances """
        self.devices()

        async def connect():
            await asyncio.gather(
                *[asyncio.create_subprocess_exec(self.adb_binary, 'connect', serial) for serial in self.serial]
            )

        asyncio.run(connect())

        return self.devices()

    def adb_replace(self, adb=None):
        """
        Different version of ADB will kill each other when starting.
        Chinese emulators (NoxPlayer, LDPlayer, MemuPlayer, MuMuPlayer) use their own adb,
        instead of the one in system PATH, so when they start they kill the adb.exe Alas is using.
        Replacing the ADB in emulator is the simplest way to solve this.

        Args:
            adb (str): Absolute path to adb.exe
        """
        self.adb_kill()
        for emulator in self.emulators:
            emulator.adb_replace(adb if adb is not None else self.adb_binary)
        self.brute_force_connect()

    def adb_recover(self):
        """ Revert adb replacement """
        self.adb_kill()
        for emulator in self.emulators:
            emulator.adb_recover()
        self.brute_force_connect()


# emu = EmulatorConnect()
# print(emu.brute_force_connect())
