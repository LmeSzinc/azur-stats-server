from module.config.utils import get_server_last_update
from module.exercise.assets import *
from module.exercise.combat import ExerciseCombat
from module.logger import logger
from module.ocr.ocr import Digit
from module.ui.ui import page_exercise

OCR_EXERCISE_REMAIN = Digit(OCR_EXERCISE_REMAIN, letter=(173, 247, 74), threshold=128)


class Exercise(ExerciseCombat):
    opponent_change_count = 0
    remain = 0

    def _new_opponent(self):
        logger.info('New opponent')
        self.appear_then_click(NEW_OPPONENT)
        self.opponent_change_count += 1

        logger.attr("Change_opponent_count", self.opponent_change_count)
        self.config.set_record(Exercise_OpponentRefreshValue=self.opponent_change_count)

        self.ensure_no_info_bar(timeout=3)

    def _opponent_fleet_check_all(self):
        if self.config.Exercise_OpponentChooseMode != 'leftmost':
            super()._opponent_fleet_check_all()

    def _opponent_sort(self, method=None):
        if method is None:
            method = self.config.Exercise_OpponentChooseMode
        if method != 'leftmost':
            return super()._opponent_sort(method=method)
        else:
            return [0, 1, 2, 3]

    def _exercise_once(self):
        """Execute exercise once.

        This method handles exercise refresh and exercise failure.

        Returns:
            bool: True if success to defeat one opponent. False if failed to defeat any opponent and refresh exhausted.
        """
        self._opponent_fleet_check_all()
        while 1:
            for opponent in self._opponent_sort():
                logger.hr(f'Opponent {opponent}', level=2)
                success = self._combat(opponent)
                if success:
                    return success

            if self.opponent_change_count >= 5:
                return False

            self._new_opponent()
            self._opponent_fleet_check_all()

    def _exercise_easiest_else_exp(self):
        """Try easiest first, if unable to beat easiest opponent then switch to max exp opponent and accept the loss.

        This method handles exercise refresh and exercise failure.

        Returns:
            bool: True if success to defeat one opponent. False if failed to defeat any opponent and refresh exhausted.
        """
        method = "easiest_else_exp"
        restore = self.config.Exercise_LowHpThreshold
        threshold = self.config.Exercise_LowHpThreshold
        self._opponent_fleet_check_all()
        while 1:
            opponents = self._opponent_sort(method=method)
            logger.hr(f'Opponent {opponents[0]}', level=2)
            self.config.override(Exercise_LowHpThreshold=threshold)
            success = self._combat(opponents[0])
            if success:
                self.config.override(Exercise_LowHpThreshold=restore)
                return success
            else:
                if self.opponent_change_count < 5:
                    logger.info("Cannot beat calculated easiest opponent, refresh")
                    self._new_opponent()
                    self._opponent_fleet_check_all()
                    continue
                else:
                    logger.info("Cannot beat calculated easiest opponent, MAX EXP then")
                    method = "max_exp"
                    threshold = 0

    def _get_opponent_change_count(self):
        """
        Same day, count set to last known change count or 6 i.e. no refresh
        New day, count set to 0 i.e. can change up to 5 times

        Returns:
            int:
        """
        record = self.config.Exercise_OpponentRefreshRecord
        update = get_server_last_update('00:00')
        if record.date() == update.date():
            # Same Day
            return self.config.Exercise_OpponentRefreshValue
        else:
            # New Day
            self.config.set_record(Exercise_OpponentRefreshValue=0)
            return 0

    def run(self):
        self.ui_ensure(page_exercise)

        self.opponent_change_count = self._get_opponent_change_count()
        logger.attr("Change_opponent_count", self.opponent_change_count)
        while 1:
            self.remain = OCR_EXERCISE_REMAIN.ocr(self.device.image)
            if self.remain <= self.config.Exercise_ExercisePreserve:
                break

            logger.hr(f'Exercise remain {self.remain}', level=1)
            if self.config.Exercise_OpponentChooseMode == "easiest_else_exp":
                success = self._exercise_easiest_else_exp()
            else:
                success = self._exercise_once()
            if not success:
                logger.info('New opponent exhausted')
                break

        # self.equipment_take_off_when_finished()

        # Scheduler
        with self.config.multi_set():
            self.config.set_record(Exercise_OpponentRefreshValue=self.opponent_change_count)
            if self.remain <= self.config.Exercise_ExercisePreserve or self.opponent_change_count >= 5:
                self.config.task_delay(server_update=True)
            else:
                self.config.task_delay(success=False)
