from module.base.button import ButtonGrid
from module.base.timer import Timer
from module.base.utils import *
from module.guild.assets import *
from module.guild.base import GuildBase
from module.logger import logger
from module.map_detection.utils import Points
from module.ocr.ocr import DigitCounter
from module.template.assets import TEMPLATE_OPERATIONS_RED_DOT

GUILD_OPERATIONS_PROGRESS = DigitCounter(OCR_GUILD_OPERATIONS_PROGRESS, letter=(255, 247, 247), threshold=64)

RECORD_OPTION_DISPATCH = ('RewardRecord', 'operations_dispatch')
RECORD_SINCE_DISPATCH = (6, 12, 18, 21,)
RECORD_OPTION_BOSS = ('RewardRecord', 'operations_boss')
RECORD_SINCE_BOSS = (0,)


class GuildOperations(GuildBase):
    def _guild_operations_ensure(self, skip_first_screenshot=True):
        """
        Ensure guild operation is loaded
        After entering guild operation, background loaded first, then dispatch/boss
        """
        confirm_timer = Timer(1.5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(GUILD_OPERATIONS_JOIN, interval=3):
                confirm_timer.reset()
                if self.image_color_count(GUILD_OPERATIONS_MONTHLY_COUNT, color=(255, 93, 90), threshold=221, count=20):
                    logger.info('Unable to join operation, no more monthly attempts left')
                    self.device.click(GUILD_OPERATIONS_CLICK_SAFE_AREA)
                else:
                    current, remain, total = GUILD_OPERATIONS_PROGRESS.ocr(self.device.image)
                    threshold = total * self.config.GUILD_OPERATIONS_JOIN_THRESHOLD
                    if current <= threshold:
                        logger.info('Joining Operation, current progress less than '
                                    f'threshold ({threshold:.2f})')
                        self.device.click(GUILD_OPERATIONS_JOIN)
                    else:
                        logger.info('Refrain from joining operation, current progress exceeds '
                                    f'threshold ({threshold:.2f})')
                        self.device.click(GUILD_OPERATIONS_CLICK_SAFE_AREA)
                continue
            if self.handle_popup_single('FLEET_UPDATED'):
                logger.info('Fleet composition altered, may still be dispatch-able. However '
                            'fellow guild members have updated their support line up.'
                            'Suggestion: Enable Boss Recommend')
                continue

            # End
            if self.appear(GUILD_BOSS_ENTER) or self.appear(GUILD_OPERATIONS_ACTIVE_CHECK, offset=(20, 20)):
                if not self.info_bar_count() and confirm_timer.reached():
                    break

    def _guild_operation_get_mode(self):
        """
        Returns:
            int: Determine which operations menu has loaded
                0 - No ongoing operations, Officers/Elites/Leader must select one to begin
                1 - Operations available, displaying a state diagram/web of operations
                2 - Guild Raid Boss active
                Otherwise None if unable to ensure or determine the menu at all

        Pages:
            in: GUILD_OPERATIONS
            out: GUILD_OPERATIONS
        """
        if self.appear(GUILD_OPERATIONS_INACTIVE_CHECK) and self.appear(GUILD_OPERATIONS_ACTIVE_CHECK):
            logger.info(
                'Mode: Operations Inactive, please contact your Elite/Officer/Leader seniors to select '
                'an operation difficulty')
            return 0
        elif self.appear(GUILD_OPERATIONS_ACTIVE_CHECK):
            logger.info('Mode: Operations Active, may proceed to scan and dispatch fleets')
            return 1
        elif self.appear(GUILD_BOSS_ENTER):
            logger.info('Mode: Guild Raid Boss')
            return 2
        else:
            logger.warning('Operations interface is unrecognized')
            return None

    def _guild_operation_get_entrance(self):
        """
        Get 2 entrance button of guild dispatch
        If operation is on the top, after clicking expand button, operation chain moves downward, and enter button
        appears on the top. So we need to detect two buttons in real time.

        Returns:
            list[Button], list[Button]: Expand button, enter button

        Pages:
            in: page_guild, guild operation, operation map (GUILD_OPERATIONS_ACTIVE_CHECK)
        """
        # Where whole operation mission chain is
        detection_area = (152, 135, 1280, 630)
        # Offset inside to avoid clicking on edge
        pad = 5

        list_expand = []
        list_enter = []
        dots = TEMPLATE_OPERATIONS_RED_DOT.match_multi(self.image_area(detection_area), threshold=5)
        logger.info(f'Active operations found: {len(dots)}')
        for button in dots:
            button = button.move(vector=detection_area[:2])
            expand = button.crop(area=(-257, 14, 12, 51), name='DISPATCH_ENTRANCE_1')
            enter = button.crop(area=(-257, -109, 12, -1), name='DISPATCH_ENTRANCE_2')
            for b in [expand, enter]:
                b.area = area_limit(b.area, detection_area)
                b._button = area_pad(b.area, pad)
            list_expand.append(expand)
            list_enter.append(enter)

        return list_expand, list_enter

    def _guild_operations_dispatch_swipe(self, skip_first_screenshot=True):
        """
        Although AL will auto focus to active dispatch, but it's bugged.
        It can't reach the operations behind.
        So this method will swipe behind, and focus to active dispatch.
        Force to use minitouch, because uiautomator2 will need longer swipes.

        Returns:
            bool: If found active dispatch.
        """
        # Where whole operation mission chain is
        detection_area = (152, 135, 1280, 630)

        for _ in range(5):
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            entrance_1, entrance_2 = self._guild_operation_get_entrance()
            if len(entrance_1):
                return True

            backup = self.config.cover(DEVICE_CONTROL_METHOD='minitouch')
            p1, p2 = random_rectangle_vector(
                (-600, 0), box=detection_area, random_range=(-50, -50, 50, 50), padding=20)
            self.device.drag(p1, p2, segments=2, shake=(0, 25), point_random=(0, 0, 0, 0), shake_random=(0, -5, 0, 5))
            backup.recover()
            self.device.sleep(0.3)

        logger.warning('Failed to find active operation dispatch')
        return False

    def _guild_operations_dispatch_enter(self, skip_first_screenshot=True):
        """
        Returns:
            bool: If entered

        Pages:
            in: page_guild, guild operation, operation map (GUILD_OPERATIONS_ACTIVE_CHECK)
                After entering guild operation, game will auto located to active operation.
                It is the main operation on chain that will be located to, side operations will be ignored.
            out: page_guild, guild operation, operation dispatch preparation (GUILD_DISPATCH_RECOMMEND)
        """
        timer_1 = Timer(2)
        timer_2 = Timer(2)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(GUILD_OPERATIONS_ACTIVE_CHECK, offset=(20, 20)):
                entrance_1, entrance_2 = self._guild_operation_get_entrance()
                if not len(entrance_1):
                    return False
                if timer_1.reached():
                    self.device.click(entrance_1[0])
                    timer_1.reset()
                    continue
                if timer_2.reached():
                    for button in entrance_2:
                        # Enter button has a black area around Easy/Normal/Hard on the upper right
                        # If operation not expanded, enter button is a background with Gaussian Blur
                        if self.image_color_count(button, color=(0, 0, 0), threshold=235, count=50):
                            self.device.click(button)
                            timer_1.reset()
                            timer_2.reset()
                            break

            if self.appear_then_click(GUILD_DISPATCH_QUICK, offset=(20, 20), interval=2):
                timer_1.reset()
                timer_2.reset()
                continue

            # End
            if self.appear(GUILD_DISPATCH_RECOMMEND, offset=(20, 20)):
                break

        return True

    def _guild_operations_get_dispatch(self):
        """
        Get the button to switch available dispatch
        In previous version, this function detects the red dot on the switch.
        But the red dot may not shows for unknown reason sometimes, so we detect the switch itself.

        Returns:
            Button: Button to switch available dispatch. None if already reach the most right fleet.

        Pages:
            in: page_guild, guild operation, operation dispatch preparation (GUILD_DISPATCH_RECOMMEND)
        """
        # Fleet switch, for 4 situation
        #          | 1 |
        #       | 1 | | 2 |
        #    | 1 | | 2 | | 3 |
        # | 1 | | 2 | | 3 | | 4 |
        #   0  1  2  3  4  5  6   buttons in switch_grid
        switch_grid = ButtonGrid(origin=(573.5, 381), delta=(20.5, 0), button_shape=(11, 24), grid_shape=(7, 1))
        # Color of inactive fleet switch
        color_active = (74, 117, 222)
        # Color of current fleet
        color_inactive = (33, 48, 66)

        text = []
        index = 0
        button = None
        for switch in switch_grid.buttons:
            if self.image_color_count(switch, color=color_inactive, threshold=235, count=30):
                index += 1
                text.append(f'| {index} |')
                button = switch
            elif self.image_color_count(switch, color=color_active, threshold=235, count=30):
                index += 1
                text.append(f'[ {index} ]')
                button = switch

        # log example: | 1 | | 2 | [ 3 ]
        text = ' '.join(text)
        logger.attr('Dispatch_fleet', text)
        if text.endswith(']'):
            logger.info('Already at the most right fleet')
            return None
        else:
            return button

    def _guild_operations_dispatch_switch_fleet(self, skip_first_screenshot=True):
        """
        Switch to the fleet on most right

        Pages:
            in: page_guild, guild operation, operation dispatch preparation (GUILD_DISPATCH_RECOMMEND)
            out: page_guild, guild operation, operation dispatch preparation (GUILD_DISPATCH_RECOMMEND)
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            button = self._guild_operations_get_dispatch()
            if button is None:
                break
            elif point_in_area((640, 393), button.area):
                logger.info('Dispatching the first fleet, skip switching')
            else:
                self.device.click(button)
                # Wait for the click animation, which will mess up _guild_operations_get_dispatch()
                self.device.sleep((0.5, 0.6))
                continue

    def _guild_operations_dispatch_execute(self, skip_first_screenshot=True):
        """
        Executes the dispatch sequence

        Pages:
            in: page_guild, guild operation, operation dispatch preparation (GUILD_DISPATCH_RECOMMEND)
            out: page_guild, guild operation, operation dispatch preparation (GUILD_DISPATCH_RECOMMEND)
        """
        dispatched = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(GUILD_DISPATCH_FLEET_UNFILLED, interval=5):
                # Don't use offset here, because GUILD_DISPATCH_FLEET_UNFILLED only has a difference in colors
                # Use long interval because the game needs a few seconds to choose the ships
                self.device.click(GUILD_DISPATCH_RECOMMEND)
                continue
            if not dispatched and self.appear_then_click(GUILD_DISPATCH_FLEET, interval=5):
                # Don't use offset here, because GUILD_DISPATCH_FLEET only has a difference in colors
                continue
            if self.handle_popup_confirm('GUILD_DISPATCH'):
                dispatched = True
                continue

            # End
            if self.appear(GUILD_DISPATCH_IN_PROGRESS):
                # In first dispatch, it will show GUILD_DISPATCH_IN_PROGRESS
                logger.info('Fleet dispatched, dispatch in progress')
                break
            if dispatched and self.appear(GUILD_DISPATCH_FLEET, interval=0):
                # In the rest of the dispatch, it will show GUILD_DISPATCH_FLEET
                # We can't ensure that fleet has dispatched,
                # because GUILD_DISPATCH_FLEET also shows after clicking recommend before dispatching
                # _guild_operations_dispatch() will retry it if haven't dispatched
                logger.info('Fleet dispatched')
                break

    def _guild_operations_dispatch_exit(self, skip_first_screenshot=True):
        """
        Exit to operation map

        Pages:
            in: page_guild, guild operation, operation dispatch preparation (GUILD_DISPATCH_RECOMMEND)
            out: page_guild, guild operation, operation map (GUILD_OPERATIONS_ACTIVE_CHECK)
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(GUILD_DISPATCH_RECOMMEND, offset=(20, 20), interval=2):
                self.device.click(GUILD_DISPATCH_CLOSE)
                continue
            if self.appear(GUILD_DISPATCH_QUICK, offset=(20, 20), interval=2):
                self.device.click(GUILD_DISPATCH_CLOSE)
                continue
            if self.appear(GUILD_DISPATCH_IN_PROGRESS, interval=2):
                # No offset here, GUILD_DISPATCH_IN_PROGRESS is a colored button
                self.device.click(GUILD_DISPATCH_CLOSE)
                continue

            # End
            if self.appear(GUILD_OPERATIONS_ACTIVE_CHECK):
                break

    def _guild_operations_dispatch(self):
        """
        Run guild dispatch

        Pages:
            in: page_guild, guild operation, operation map (GUILD_OPERATIONS_ACTIVE_CHECK)
            out: page_guild, guild operation, operation map (GUILD_OPERATIONS_ACTIVE_CHECK)
        """
        logger.hr('Guild dispatch')
        if not self._guild_operations_dispatch_swipe():
            return False

        for _ in range(5):
            if self._guild_operations_dispatch_enter():
                self._guild_operations_dispatch_switch_fleet()
                self._guild_operations_dispatch_execute()
                self._guild_operations_dispatch_exit()
            else:
                return True

        logger.warning('Too many trials on guild operation dispatch')
        return False

    def _guild_operations_boss_preparation(self, az, skip_first_screenshot=True):
        """
        Execute preparation sequence for guild raid boss

        az is a GuildCombat instance to handle combat various
        interfaces. Independently created to avoid conflicts
        or override methods of parent/child objects

        Pages:
            in: GUILD_OPERATIONS_BOSS
            out: IN_BATTLE
        """
        is_loading = False
        dispatch_count = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(GUILD_BOSS_ENTER, interval=3):
                continue

            if self.appear(GUILD_DISPATCH_FLEET, interval=3):
                # Button does not appear greyed out even
                # when empty fleet composition
                if dispatch_count < 5:
                    self.device.click(GUILD_DISPATCH_FLEET)
                    dispatch_count += 1
                else:
                    logger.warning('Fleet composition error. Preloaded guild support selection may be '
                                   'preventing dispatch. Suggestion: Enable Boss Recommend')
                    return False
                continue

            if self.config.ENABLE_GUILD_OPERATIONS_BOSS_RECOMMEND:
                if self.info_bar_count() and self.appear_then_click(GUILD_DISPATCH_RECOMMEND_2, interval=3):
                    continue

            # Only print once when detected
            if not is_loading:
                if az.is_combat_loading():
                    is_loading = True
                    continue

            if az.handle_combat_automation_confirm():
                continue

            # End
            if az.is_combat_executing():
                return True

    def _guild_operations_boss_combat(self):
        """
        Execute combat sequence
        If battle could not be prepared, exit

        Pages:
            in: GUILD_OPERATIONS_BOSS
            out: GUILD_OPERATIONS_BOSS
        """
        from module.guild.guild_combat import GuildCombat
        az = GuildCombat(self.config, device=self.device)

        if not self._guild_operations_boss_preparation(az):
            return False
        backup = self.config.cover(SUBMARINE=1, SUBMARINE_MODE='every_combat')
        az.combat_execute(auto='combat_auto')
        backup.recover()
        az.combat_status(expected_end='in_ui')
        logger.info('Guild Raid Boss has been repelled')
        return True

    def _guild_operations_boss_available(self):
        """
        Returns:
            bool:
        """
        appear = self.image_color_count(GUILD_BOSS_AVAILABLE, color=(140, 243, 99), threshold=221, count=10)
        if appear:
            logger.info('Guild boss available')
        else:
            logger.info('Guild boss not available')
        return appear

    def guild_operations(self):
        if not self.guild_side_navbar_ensure(bottom=1):
            logger.info('Operations sidebar not ensured, try again on next reward loop')
            return None
        self._guild_operations_ensure()
        # Determine the mode of operations, currently 3 are available
        operations_mode = self._guild_operation_get_mode()
        if operations_mode is None:
            return

        # Execute actions based on the detected mode
        if operations_mode == 0:
            return
        elif operations_mode == 1:
            self._guild_operations_dispatch()
            self.config.record_save(option=RECORD_OPTION_DISPATCH)
        else:
            # Limit check for Guild Raid Boss to once a day
            if not self.config.record_executed_since(option=RECORD_OPTION_BOSS, since=RECORD_SINCE_BOSS):
                skip_record = False
                if self._guild_operations_boss_available():
                    if self.config.ENABLE_GUILD_OPERATIONS_BOSS_AUTO:
                        if not self._guild_operations_boss_combat():
                            skip_record = True
                    else:
                        logger.info('Auto-battle disabled, play manually to complete this Guild Task')

                if not skip_record:
                    self.config.record_save(option=RECORD_OPTION_BOSS)
