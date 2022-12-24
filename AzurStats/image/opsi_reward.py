from AzurStats.image.auto_search_reward import AutoSearchReward
from module.os_handler.assets import AUTO_SEARCH_REWARD


class OpsiReward(AutoSearchReward):
    def is_opsi_reward(self, image) -> bool:
        return bool(self.classify_server(AUTO_SEARCH_REWARD, image, offset=(50, 50)))
