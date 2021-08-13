from scipy import signal

from module.base.base import ModuleBase
from module.base.button import Button
from module.base.timer import Timer
from module.base.utils import *
from module.handler.assets import *
from module.logger import logger


def info_letter_preprocess(image):
    """
    Args:
        image (np.ndarray):

    Returns:
        np.ndarray
    """
    image = image.astype(float)
    image = (image - 64) / 0.75
    image[image > 255] = 255
    image[image < 0] = 0
    image = image.astype('uint8')
    return image


class InfoHandler(ModuleBase):
    """
    Class to handle all kinds of message.
    """
    """
    Info bar
    """

    def info_bar_count(self):
        if self.appear(INFO_BAR_3):
            return 3
        elif self.appear(INFO_BAR_2):
            return 2
        elif self.appear(INFO_BAR_1):
            return 1
        else:
            return 0

    def handle_info_bar(self):
        if self.info_bar_count():
            self.wait_until_disappear(INFO_BAR_1)
            return True
        else:
            return False

    def ensure_no_info_bar(self, timeout=0.6):
        timeout = Timer(timeout)
        timeout.start()
        while 1:
            self.device.screenshot()
            self.handle_info_bar()

            if timeout.reached():
                break

    """
    Popup info
    """
    _popup_offset = (3, 30)

    def handle_popup_confirm(self, name=''):
        if self.appear(POPUP_CANCEL, offset=self._popup_offset) \
                and self.appear(POPUP_CONFIRM, offset=self._popup_offset, interval=2):
            POPUP_CONFIRM.name = POPUP_CONFIRM.name + '_' + name
            self.device.click(POPUP_CONFIRM)
            POPUP_CONFIRM.name = POPUP_CONFIRM.name[:-len(name) - 1]
            return True
        else:
            return False

    def handle_popup_cancel(self, name=''):
        if self.appear(POPUP_CONFIRM, offset=self._popup_offset) \
                and self.appear(POPUP_CANCEL, offset=self._popup_offset, interval=2):
            POPUP_CANCEL.name = POPUP_CANCEL.name + '_' + name
            self.device.click(POPUP_CANCEL)
            POPUP_CANCEL.name = POPUP_CANCEL.name[:-len(name) - 1]
            return True
        else:
            return False

    def handle_popup_single(self, name=''):
        if self.appear(GET_MISSION, offset=self._popup_offset, interval=2):
            prev_name = GET_MISSION.name
            GET_MISSION.name = POPUP_CONFIRM.name + '_' + name
            self.device.click(GET_MISSION)
            GET_MISSION.name = prev_name
            return True

        return False

    def handle_urgent_commission(self, save_get_items=None):
        """
        Args:
            save_get_items (bool):

        Returns:
            bool:
        """
        if save_get_items is None:
            save_get_items = self.config.ENABLE_SAVE_GET_ITEMS

        appear = self.appear(GET_MISSION, offset=True, interval=2)
        if appear:
            logger.info('Get urgent commission')
            if save_get_items:
                self.handle_info_bar()
                self.device.save_screenshot('get_mission')
            self.device.click(GET_MISSION)
        return appear

    def handle_combat_low_emotion(self):
        if not self.config.IGNORE_LOW_EMOTION_WARN:
            return False

        return self.handle_popup_confirm('IGNORE_LOW_EMOTION')

    def handle_use_data_key(self):
        if not self.config.USE_DATA_KEY:
            return False

        if not self.appear(POPUP_CONFIRM, offset=self._popup_offset) \
                and not self.appear(POPUP_CANCEL, offset=self._popup_offset, interval=2):
            return False

        if self.appear(USE_DATA_KEY, offset=(20, 20)):
            self.device.click(USE_DATA_KEY_NOTIFIED)
            self.device.sleep((0.5, 0.8))
            return self.handle_popup_confirm('USE_DATA_KEY')

        return False

    """
    Guild popup info
    """
    def handle_guild_popup_confirm(self):
        if self.appear(GUILD_POPUP_CANCEL, offset=self._popup_offset) \
                and self.appear(GUILD_POPUP_CONFIRM, offset=self._popup_offset, interval=2):
            self.device.click(GUILD_POPUP_CONFIRM)
            return True

        return False

    def handle_guild_popup_cancel(self):
        if self.appear(GUILD_POPUP_CONFIRM, offset=self._popup_offset) \
                and self.appear(GUILD_POPUP_CANCEL, offset=self._popup_offset, interval=2):
            self.device.click(GUILD_POPUP_CANCEL)
            return True

        return False

    """
    Mission popup info
    """
    def handle_mission_popup_go(self):
        if self.appear(MISSION_POPUP_ACK, offset=self._popup_offset) \
                and self.appear(MISSION_POPUP_GO, offset=self._popup_offset, interval=2):
            self.device.click(MISSION_POPUP_GO)
            return True

        return False

    def handle_mission_popup_ack(self):
        if self.appear(MISSION_POPUP_GO, offset=self._popup_offset) \
                and self.appear(MISSION_POPUP_ACK, offset=self._popup_offset, interval=2):
            self.device.click(MISSION_POPUP_ACK)
            return True

        return False

    """
    Story
    """
    story_popup_timout = Timer(10, count=20)
    map_has_fast_forward = False  # Will be override in fast_forward.py

    # Area to detect the options, should include at least 3 options.
    _story_option_area = (730, 188, 1140, 480)
    # Background color of the left part of the option.
    _story_option_color = (99, 121, 156)
    _story_option_timer = Timer(2)

    def _story_option_buttons(self):
        """
        Returns:
            list[Button]: List of story options, from upper to bottom. If no option found, return an empty list.
        """
        image = color_similarity_2d(self.image_area(self._story_option_area), color=self._story_option_color) > 225
        x_count = np.where(np.sum(image, axis=0) > 40)[0]
        if not len(x_count):
            return []
        x_min, x_max = np.min(x_count), np.max(x_count)

        parameters = {
            # Option is 300`320px x 50~52px.
            'height': 280,
            'width': 45,
            'distance': 50,
            # Chooses the relative height at which the peak width is measured as a percentage of its prominence.
            # 1.0 calculates the width of the peak at its lowest contour line,
            # while 0.5 evaluates at half the prominence height.
            # Must be at least 0.
            'rel_height': 5,
        }
        y_count = np.sum(image, axis=1)
        peaks, properties = signal.find_peaks(y_count, **parameters)
        buttons = []
        total = len(peaks)
        if not total:
            return []
        for n, bases in enumerate(zip(properties['left_bases'], properties['right_bases'])):
            area = (x_min, bases[0], x_max, bases[1])
            area = area_pad(area_offset(area, offset=self._story_option_area[:2]), pad=5)
            buttons.append(
                Button(area=area, color=self._story_option_color, button=area, name=f'STORY_OPTION_{n + 1}_OF_{total}'))

        return buttons

    def story_skip(self):
        if self.story_popup_timout.started() and not self.story_popup_timout.reached():
            if self.handle_popup_confirm('STORY_SKIP'):
                self.story_popup_timout = Timer(10)
                self.interval_reset(STORY_SKIP)
                self.interval_reset(STORY_LETTERS_ONLY)
                return True
        if self.appear(STORY_LETTER_BLACK) and self.appear_then_click(STORY_LETTERS_ONLY, offset=True, interval=2):
            self.story_popup_timout.reset()
            return True
        if self._story_option_timer.reached() and self.appear(STORY_SKIP, offset=True, interval=0):
            options = self._story_option_buttons()
            if len(options):
                self.device.click(options[0])
                self._story_option_timer.reset()
                self.story_popup_timout.reset()
                self.interval_reset(STORY_SKIP)
                self.interval_reset(STORY_LETTERS_ONLY)
                return True
        if self.appear_then_click(STORY_SKIP, offset=True, interval=2):
            self.story_popup_timout.reset()
            return True
        if self.appear_then_click(GAME_TIPS, offset=(20, 20), interval=2):
            self.story_popup_timout.reset()
            return True

        return False

    def handle_story_skip(self):
        if self.map_has_fast_forward:
            return False

        return self.story_skip()

    def ensure_no_story(self, skip_first_screenshot=True):
        logger.info('Ensure no story')
        story_timer = Timer(3, count=6).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.story_skip():
                story_timer.reset()

            if story_timer.reached():
                break

    def handle_map_after_combat_story(self):
        if not self.config.MAP_HAS_MAP_STORY:
            return False

        self.ensure_no_story()
