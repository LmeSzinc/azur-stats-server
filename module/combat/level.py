from module.base.base import ModuleBase
from module.base.button import *
from module.base.decorator import Config
from module.logger import logger
from module.ocr.ocr import Digit

COLOR_WHITE = (255, 255, 255)
COLOR_MASKED = (107, 105, 107)


class Level(ModuleBase):
    _lv = []
    _lv_before_battle = []

    @property
    def lv(self):
        """
        Returns:
            list[int]:
        """
        return self._lv

    @lv.setter
    def lv(self, value):
        """
        Args:
            value (list[int]):
        """
        self._lv = value

    def lv_reset(self):
        """
        Call this method after enter map.
        """
        self._lv = [-1] * 6
        self._lv_before_battle = [-1] * 6

    @Config.when(SERVER='en')
    def _lv_grid(self):
        return ButtonGrid(origin=(56, 113), delta=(0, 100), button_shape=(46, 19), grid_shape=(1, 6))

    @Config.when(SERVER='jp')
    def _lv_grid(self):
        return ButtonGrid(origin=(58, 128), delta=(0, 100), button_shape=(46, 19), grid_shape=(1, 6))

    @Config.when(SERVER=None)
    def _lv_grid(self):
        return ButtonGrid(origin=(58, 128), delta=(0, 100), button_shape=(46, 19), grid_shape=(1, 6))

    def lv_get(self, after_battle=False):
        """
        Args:
            after_battle (bool): True if called after battle else False.

        Returns:
            list[int]:
        """
        if not self.config.STOP_IF_REACH_LV120 and not self.config.STOP_IF_REACH_LV32:
            return [-1] * 6

        self._lv_before_battle = self.lv if after_battle else [-1] * 6

        ocr = LevelOcr(self._lv_grid().buttons, name='LevelOcr')
        self.lv = ocr.ocr(self.device.image)
        logger.attr('LEVEL', ', '.join(str(data) for data in self.lv))

        if after_battle:
            self.lv120_triggered()
            self.lv32_triggered()

        return self.lv

    def lv120_triggered(self):
        if not self.config.STOP_IF_REACH_LV120:
            return False

        for i in range(6):
            if self.lv[i] == 120 and self._lv_before_battle[i] == 119:
                logger.info(f'Position {i} LV.120 Reached')
                self.config.LV120_TRIGGERED = True
                return True

        return False

    def lv32_triggered(self):
        if not self.config.STOP_IF_REACH_LV32:
            return False

        if self.lv[0] >= 32:
            logger.info(f'Position 0 LV.32 Reached')
            self.config.LV32_TRIGGERED = True
            return True

        return False


class LevelOcr(Digit):
    def pre_process(self, image):
        # Check the max value of red channel to find out whether the image is masked.
        # It would be no larger than COLOR_MASKED[0]=107 iff masked.
        # Crop before checking to cut off the "need repair" icon while preserving upper part of char 'V'.
        max_red = image[:8, :, 0].max()
        if max_red <= COLOR_MASKED[0]:
            # The mask on low hp ships turns COLOR_WHITE=(255, 255, 255) to COLOR_MASKED=(107, 105, 107),
            # so multiply all channels by a scalar can turn them back.
            scalar = np.mean(COLOR_WHITE) / np.mean(COLOR_MASKED)
            image = cv2.addWeighted(image, scalar, image, 0, 0)

        # Deal with the blue background of chars before converting to greyscale.
        # The background is semi-transparent. It turns (0, 0, 0) to (33, 65, 115), and (255, 255, 255)
        # to (107, 138, 189). We use the middle point (70, 102, 152).
        bg = (70, 102, 152)
        # BT.601
        luma_trans = (0.299, 0.587, 0.114)
        luma_bg = np.dot(bg, luma_trans)
        image = cv2.subtract(image, (*bg, 0)).dot(luma_trans).round().astype(np.uint8)
        image = cv2.subtract(255, cv2.multiply(image, 255 / (255 - luma_bg)))
        # Find 'L' to strip 'LV.'.
        # Return an empty image if 'L' is not found.
        letter_l = np.nonzero(image[9:15, :].max(axis=0) < 127)[0]
        if len(letter_l):
            first_digit = letter_l[0] + 17
            if first_digit + 3 < 46:  # LV_GRID_MAIN.button_shape[0] = 46
                return image[:, first_digit:]
        return np.array([[255]], dtype=np.uint8)
