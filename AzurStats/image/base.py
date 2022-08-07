import typing as t

import numpy as np

from module.base.button import Button
from module.base.utils import color_similarity_2d, crop
from module.combat.assets import GET_ITEMS_1, GET_ITEMS_3, GET_ITEMS_3_CHECK

# Key: Button object to cache
# Value: dict
#     Key: str, server name
#     Value: Button object of the specific server
CLASSIFY_CACHE: t.Dict[Button, t.Dict[str, Button]] = {}


class ImageBase:
    """
    Base class to detect a single screen shot
    """
    # cn, en, jp, tw, or '' if button not appear
    # This value if set at the first time classify_server() called
    server: str = ''

    def classify_server(self, button, image, offset=(20, 20)):
        """
        Get server name if a button appear on image

        Args:
            button (Button):
            image: Screenshot to detect, or None to use the `self.image`
            offset:

        Returns:
            str: cn, en, jp, tw, or '' if button not appear
        """
        if button not in CLASSIFY_CACHE:
            CLASSIFY_CACHE[button] = button.split_server()

        for server, server_button in CLASSIFY_CACHE[button].items():
            if server_button.match(image, offset=offset):
                if not self.server:
                    self.server = server
                return server

        # No match
        if not self.server:
            self.server = ''
        return ''

    def image_color_count(self, image, button, color, threshold=221, count=50):
        """
        Args:
            image:
            button (Button, tuple): Button instance or area.
            color (tuple): RGB.
            threshold: 255 means colors are the same, the lower the worse.
            count (int): Pixels count.

        Returns:
            bool:
        """
        if isinstance(button, Button):
            image = crop(image, button.area)
        else:
            image = crop(image, button)
        mask = color_similarity_2d(image, color=color) > threshold
        return np.sum(mask) > count

    def get_items_count(self, image):
        """
        Args:
            image:

        Returns:
            int: Rows of get items, 1 to 3, or 0 if it's not a get_items image
        """
        if GET_ITEMS_3.match(image, offset=(5, 5)):
            if self.image_color_count(image, GET_ITEMS_3_CHECK, color=(255, 255, 255), threshold=221, count=100):
                return 3
            else:
                return 2
        if GET_ITEMS_1.match(image, offset=(5, 5)):
            return 1
        return 0
