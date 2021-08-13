from module.base.base import ModuleBase
from module.combat.assets import *
from module.base.timer import Timer
from module.logger import logger


class SubmarineCall(ModuleBase):
    submarine_call_flag = False
    submarine_call_timer = Timer(5)
    submarine_call_click_timer = Timer(1)

    def submarine_call_reset(self):
        """
        Call this method after in battle_execute.
        """
        self.submarine_call_timer.reset()
        self.submarine_call_flag = False

    def handle_submarine_call(self):
        """
        Returns:
            bool: If call.
        """
        if self.submarine_call_flag:
            return False
        if not self.config.SUBMARINE or self.config.SUBMARINE_MODE in ['do_not_use', 'hunt_only']:
            self.submarine_call_flag = True
            return False
        if self.submarine_call_timer.reached():
            logger.info('Submarine call timer reached')
            self.submarine_call_flag = True
            return False

        if not self.appear(SUBMARINE_AVAILABLE_CHECK_1) or not self.appear(SUBMARINE_AVAILABLE_CHECK_2):
            return False

        if self.appear(SUBMARINE_CALLED):
            logger.info('Submarine called')
            self.submarine_call_flag = True
            return False
        elif self.submarine_call_click_timer.reached():
            if self.appear_then_click(SUBMARINE_READY):
                logger.info('Call submarine')
                return True
            else:
                logger.info('Incorrect submarine icon')
                self.device.click(SUBMARINE_READY)
                logger.info('Call submarine')
                return True
