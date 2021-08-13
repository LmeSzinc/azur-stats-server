from module.combat.combat import *
from module.exercise.assets import *
from module.exercise.equipment import ExerciseEquipment
from module.exercise.hp_daemon import HpDaemon
from module.exercise.opponent import OpponentChoose, OPPONENT
from module.ui.assets import EXERCISE_CHECK


class ExerciseCombat(HpDaemon, OpponentChoose, ExerciseEquipment):
    def _in_exercise(self):
        return self.appear(EXERCISE_CHECK, offset=(20, 20))

    def is_combat_executing(self):
        """
        Returns:
            bool:
        """
        return self.appear(PAUSE) and np.max(self.device.image.crop(PAUSE_DOUBLE_CHECK.area)) < 153

    def _combat_preparation(self):
        logger.info('Combat preparation')
        while 1:
            self.device.screenshot()
            if self.appear(BATTLE_PREPARATION):

                self.equipment_take_on()
                pass

                self.device.click(BATTLE_PREPARATION)
                continue

            # End
            if self.appear(PAUSE):
                break

    def _combat_execute(self):
        """
        Returns:
            bool: True if wins. False if quit.
        """
        logger.info('Combat execute')
        self.low_hp_confirm_timer = Timer(self.config.LOW_HP_CONFIRM_WAIT, count=2).start()
        show_hp_timer = Timer(5)
        success = True
        end = False

        while 1:
            self.device.screenshot()

            if not self.is_combat_executing():
                # Finish - S or D rank
                if self.appear_then_click(BATTLE_STATUS_S):
                    success = True
                    end = True
                    continue
                if self.appear_then_click(BATTLE_STATUS_D):
                    success = True
                    end = True
                    logger.info("Exercise LOST")
                    self.device.send_notification('Exercises', 'Exercise LOST')
                    continue
            if self.appear_then_click(GET_ITEMS_1):
                continue
            if self.appear(EXP_INFO_S):
                self.device.click(CLICK_SAFE_AREA)
                continue
            if self.appear(EXP_INFO_D):
                self.device.click(CLICK_SAFE_AREA)
                continue
            # Last D rank screen
            if self.appear_then_click(OPTS_INFO_D, offset=(30, 30)):
                continue

            # Quit
            if not end:
                if self._at_low_hp(image=self.device.image):
                    logger.info('Exercise quit')
                    if self.appear_then_click(PAUSE):
                        self.device.sleep(0.3)
                        continue
                else:
                    if show_hp_timer.reached():
                        show_hp_timer.reset()
                        self._show_hp()

            if self.appear_then_click(QUIT_CONFIRM, offset=(20, 20), interval=5):
                success = False
                end = True
                continue

            if self.appear_then_click(QUIT_RECONFIRM, offset=True, interval=5):
                self.interval_reset(QUIT_CONFIRM)
                continue

            # End
            if end and self._in_exercise() or self.appear(BATTLE_PREPARATION):
                logger.hr('Combat end')
                break

        return success

    def _choose_opponent(self, index):
        """
        Args:
            index (int): From left to right. 0 to 3.
        """
        logger.hr('Opponent: %s' % str(index))
        opponent_timer = Timer(5)
        preparation_timer = Timer(5)

        while 1:
            self.device.screenshot()

            if opponent_timer.reached() and self._in_exercise():
                self.device.click(OPPONENT[index, 0])
                opponent_timer.reset()

            if preparation_timer.reached() and self.appear_then_click(EXERCISE_PREPARATION):
                # self.device.sleep(0.3)
                preparation_timer.reset()
                opponent_timer.reset()
                continue

            # End
            if self.appear(BATTLE_PREPARATION):
                break

    def _preparation_quit(self):
        logger.info('Preparation quit')
        self.ui_back(check_button=self._in_exercise, appear_button=BATTLE_PREPARATION)

    def _combat(self, opponent):
        """
        Args:
            opponent(int): From left to right. 0 to 3.

        Returns:
            bool: True if wins. False if challenge times exhausted.
        """
        self._choose_opponent(opponent)

        for n in range(1, self.config.OPPONENT_CHALLENGE_TRIAL + 1):
            logger.hr('Try: %s' % n)
            self._combat_preparation()
            success = self._combat_execute()
            if success:
                return success

        self._preparation_quit()
        return False

    def equipment_take_off_when_finished(self):
        if self.config.EXERCISE_FLEET_EQUIPMENT is None:
            return False
        if not self.equipment_has_take_on:
            return False

        self._choose_opponent(0)
        super().equipment_take_off()
        self._preparation_quit()

    # def equipment_take_on(self):
    #     if self.config.EXERCISE_FLEET_EQUIPMENT is None:
    #         return False
    #     if self.equipment_has_take_on:
    #         return False
    #
    #     self._choose_opponent(0)
    #     super().equipment_take_on()
    #     self._preparation_quit()
