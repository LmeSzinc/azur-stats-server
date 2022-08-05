import logging

from deploy.config import DeployConfig
from deploy.emulator import EmulatorConnect
from deploy.logger import logger
from deploy.utils import *


def show_fix_tip(module):
    logger.info(f"""
    To fix this:
    1. Open console.bat
    2. Execute the following commands:
        pip uninstall -y {module}
        pip install --no-cache-dir {module}
    3. Re-open Alas.exe
    """)


class AdbManager(DeployConfig):
    @cached_property
    def adb(self):
        return self.filepath('AdbExecutable')

    def adb_install(self):
        logger.hr('Start ADB service', 0)

        emulator = EmulatorConnect(adb=self.adb)
        if self.ReplaceAdb:
            logger.hr('Replace ADB', 1)
            emulator.adb_replace()
        elif self.AutoConnect:
            logger.hr('ADB Connect', 1)
            emulator.brute_force_connect()

        if self.InstallUiautomator2:
            logger.hr('Uiautomator2 Init', 1)
            try:
                import adbutils
            except ModuleNotFoundError as e:
                message = str(e)
                for module in ['apkutils2', 'progress']:
                    # ModuleNotFoundError: No module named 'apkutils2'
                    # ModuleNotFoundError: No module named 'progress.bar'
                    if module in message:
                        show_fix_tip(module)
                        exit(1)

            # Remove global proxies, or uiautomator2 will go through it
            for k in list(os.environ.keys()):
                if k.lower().endswith('_proxy'):
                    del os.environ[k]

            from uiautomator2.init import Initer
            for device in adbutils.adb.iter_device():
                init = Initer(device, loglevel=logging.DEBUG)
                init.set_atx_agent_addr('127.0.0.1:7912')
                try:
                    init.install()
                except AssertionError:
                    logger.info(f'AssertionError when installing uiautomator2 on device {device.serial}')
                    logger.info('If you are using BlueStacks or LD player or WSA, '
                          'please enable ADB in the settings of your emulator')
                    exit(1)
                init._device.shell(["rm", "/data/local/tmp/minicap"])
                init._device.shell(["rm", "/data/local/tmp/minicap.so"])
