from module.base.timer import Timer
from module.campaign.run import OCR_OIL
from module.combat.assets import GET_ITEMS_1, GET_ITEMS_2
from module.logger import logger
from module.supply_pack.assets import *
from module.ui.page import page_supply_pack
from module.ui.ui import UI


class SupplyPack(UI):
    def supply_pack_buy(self, supply_pack, skip_first_screenshot=True):
        """
        Args:
            supply_pack (Button): Button of supply pack, click to buy.
            skip_first_screenshot (bool):

        Returns:
            bool: If bought.
        """
        logger.hr('Supply pack buy')
        [self.interval_clear(asset) for asset in [GET_ITEMS_1, GET_ITEMS_2, supply_pack, BUY_CONFIRM]]

        logger.info(f'Buying {supply_pack}')
        executed = False
        confirm_timer = Timer(1, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(supply_pack, offset=(20, 20), interval=3):
                confirm_timer.reset()
                continue
            if self.appear_then_click(BUY_CONFIRM, offset=(20, 20), interval=3):
                confirm_timer.reset()
                continue
            if self.handle_popup_confirm('BUY_SUPPLY_PACK'):
                self.interval_reset(supply_pack)
                self.interval_reset(BUY_CONFIRM)
                executed = True
                continue
            for button in [GET_ITEMS_1, GET_ITEMS_2]:
                if self.appear_then_click(button, offset=(30, 30), interval=3):
                    confirm_timer.reset()
                    continue

            # End
            if self.appear(page_supply_pack.check_button, offset=(20, 20)) \
                    and not self.appear(supply_pack, offset=(20, 20)):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

        logger.info(f'Supply pack buy finished, executed={executed}')
        return executed

    def run(self):
        """
        Pages:
            in: Any page
            out: page_supply_pack, supply pack tab
        """
        self.ui_ensure(page_supply_pack)

        oil = OCR_OIL.ocr(self.device.image)
        if oil <= 21000:
            self.supply_pack_buy(FREE_SUPPLY_PACK)
        else:
            logger.info('Oil > 21000, unable to buy free weekly supply pack')

        self.config.task_delay(server_update=True)
