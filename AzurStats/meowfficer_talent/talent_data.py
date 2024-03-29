import re

DICT_MEOWFFICER_TALENT = {
    ("既定的命运", 0, "既定的命运"): re.compile("雷击航空.{1,3}10.*幸运.{1,3}3"),
    ("小小的奇迹", 0, "小小的奇迹"): re.compile("舰队幸运.{1,3}5"),
    ("不动如山", 0, "不动如山"): re.compile("受到伤害.{1,3}3"),
    ("侵略如火", 0, "侵略如火"): re.compile("造成伤害.{1,3}3"),
    ("其徐如林", 0, "其徐如林"): re.compile("防空反潜.{1,3}15.*机动.{1,3}3"),
    ("其疾如风", 0, "其疾如风"): re.compile("舰队航速.{1,3}3"),
    ("最佳玩伴", 0, "最佳玩伴"): re.compile("提供经验.{1,3}10"),
    ("被期待的新星", 0, "被期待的新星"): re.compile("的经验值.{1,3}10"),
    ("狼群之首", 0, "狼群之首"): re.compile("潜母雷击.{1,3}15.*装填.{1,3}8"),
    ("王牌机师", 0, "王牌机师"): re.compile("正航航空.{1,3}15.*装填.{1,3}8"),
    ("水雷魂", 0, "水雷魂"): re.compile("轻巡雷击.{1,3}15.*击率.{1,3}3"),
    ("一发入魂", 0, "一发入魂"): re.compile("战列炮击.{1,3}15.*击率.{1,3}3"),
    ("见敌必战", 0, "见敌必战"): re.compile("超巡炮击.{1,3}10.*装填.{1,3}12"),
    ("铁血指挥", 3, "王牌指挥官铁血"): re.compile("铁血炮击.{1,3}12.*命中.{1,3}3"),
    ("铁血指挥", 2, "精锐指挥官铁血"): re.compile("铁血炮击.{1,3}8.*命中.{1,3}2"),
    ("铁血指挥", 1, "新晋指挥官铁血"): re.compile("铁血炮击.{1,3}6.*命中.{1,3}1"),
    ("重樱指挥", 3, "王牌指挥官重樱"): re.compile("重樱雷击.{1,3}16.*机动.{1,3}3"),
    ("重樱指挥", 2, "精锐指挥官重樱"): re.compile("重樱雷击.{1,3}11.*机动.{1,3}2"),
    ("重樱指挥", 1, "新晋指挥官重樱"): re.compile("重樱雷击.{1,3}8.*机动.{1,3}1"),
    ("皇家指挥", 3, "王牌指挥官皇家"): re.compile("皇家炮击.{1,3}14.*机动.{1,3}3"),
    ("皇家指挥", 2, "精锐指挥官皇家"): re.compile("皇家炮击.{1,3}10.*机动.{1,3}2"),
    ("皇家指挥", 1, "新晋指挥官皇家"): re.compile("皇家炮击.{1,3}7.*机动.{1,3}1"),
    ("白鹰指挥", 3, "王牌指挥官白鹰"): re.compile("白鹰防空.{1,3}16.*装填.{1,3}6"),
    ("白鹰指挥", 2, "精锐指挥官白鹰"): re.compile("白鹰防空.{1,3}11.*装填.{1,3}4"),
    ("白鹰指挥", 1, "新晋指挥官白鹰"): re.compile("白鹰防空.{1,3}8.*装填.{1,3}3"),
    ("潜艇雷击装填", 3, "沉默杀手"): re.compile("潜母雷击.{1,3}20.*装填.{1,3}6"),
    ("潜艇雷击装填", 2, "精锐指挥官潜艇"): re.compile("潜母雷击.{1,3}14.*装填.{1,3}4"),
    ("潜艇雷击装填", 1, "新晋指挥官潜艇"): re.compile("潜母雷击.{1,3}10.*装填.{1,3}3"),
    ("航母航空装填", 3, "苍穹猎手"): re.compile("正航航空.{1,3}20.*装填.{1,3}6"),
    ("航母航空装填", 2, "精锐指挥官空母"): re.compile("正航航空.{1,3}14.*装填.{1,3}4"),
    ("航母航空装填", 1, "新晋指挥官空母"): re.compile("正航航空.{1,3}10.*装填.{1,3}3"),
    ("战列耐久炮击", 3, "钢铁巨兽"): re.compile("战列耐久.{1,3}10.*炮击.{1,3}16"),
    ("战列耐久炮击", 2, "精锐指挥官战列"): re.compile("战列耐久.{1,3}70.*炮击.{1,3}11"),
    ("战列耐久炮击", 1, "新晋指挥官战列"): re.compile("战列耐久.{1,3}50.*炮击.{1,3}8"),
    ("巡洋炮击雷击", 3, "中坚力量"): re.compile("超巡炮击.{1,3}10.*雷击.{1,3}10"),
    ("巡洋炮击雷击", 2, "精锐指挥官巡洋"): re.compile("超巡炮击.{1,3}7.*雷击.{1,3}7"),
    ("巡洋炮击雷击", 1, "新晋指挥官巡洋"): re.compile("超巡炮击.{1,3}5.*雷击.{1,3}5"),
    ("驱逐雷击装填", 3, "海上先锋"): re.compile("驱逐雷击.{1,3}16.*装填.{1,3}8"),
    ("驱逐雷击装填", 2, "精锐指挥官驱逐"): re.compile("驱逐雷击.{1,3}11.*装填.{1,3}5"),
    ("驱逐雷击装填", 1, "新晋指挥官驱逐"): re.compile("驱逐雷击.{1,3}8.*装填.{1,3}4"),
    ("巡洋机动", 3, "航海长大型舰"): re.compile("超巡机动.{1,3}3"),
    ("巡洋机动", 2, "熟练舵手大型舰"): re.compile("超巡机动.{1,3}2"),
    ("巡洋机动", 1, "操舵手大型舰"): re.compile("超巡机动.{1,3}1"),
    ("运输机动", 3, "航海长中型舰"): re.compile("运输机动.{1,3}6"),
    ("运输机动", 2, "熟练舵手中型舰"): re.compile("运输机动.{1,3}4"),
    ("运输机动", 1, "操舵手中型舰"): re.compile("运输机动.{1,3}3"),
    ("驱逐机动", 3, "航海长小型舰"): re.compile("驱逐机动.{1,3}10"),
    ("驱逐机动", 2, "熟练舵手小型舰"): re.compile("驱逐机动.{1,3}7"),
    ("驱逐机动", 1, "操舵手小型舰"): re.compile("驱逐机动.{1,3}5"),
    ("主力命中", 3, "鹰眼主力"): re.compile("主力命中.{1,3}3"),
    ("主力命中", 2, "熟练观测士主力"): re.compile("主力命中.{1,3}2"),
    ("主力命中", 1, "新手观测士主力"): re.compile("主力命中.{1,3}1"),
    ("先锋命中", 3, "鹰眼先锋"): re.compile("先锋命中.{1,3}6"),
    ("先锋命中", 2, "熟练观测士先锋"): re.compile("先锋命中.{1,3}4"),
    ("先锋命中", 1, "新手观测士先锋"): re.compile("先锋命中.{1,3}3"),
    ("潜艇命中", 3, "鹰眼潜艇"): re.compile("潜母命中.{1,3}5"),
    ("潜艇命中", 2, "熟练观测士潜艇"): re.compile("潜母命中.{1,3}3"),
    ("潜艇命中", 1, "新手观测士潜艇"): re.compile("潜母命中.{1,3}2"),
    ("运输耐久", 3, "轮机长特殊"): re.compile("运输耐久.{1,3}80"),
    ("运输耐久", 2, "熟练轮机手特殊"): re.compile("运输耐久.{1,3}56"),
    ("运输耐久", 1, "轮机手特殊"): re.compile("运输耐久.{1,3}40"),
    ("航母耐久", 3, "轮机长空母"): re.compile("正航耐久.{1,3}10"),
    ("航母耐久", 2, "熟练轮机手空母"): re.compile("正航耐久.{1,3}70"),
    ("航母耐久", 1, "轮机手空母"): re.compile("正航耐久.{1,3}50"),
    ("航战耐久", 3, "轮机长战列"): re.compile("航战耐久.{1,3}15"),
    ("航战耐久", 2, "熟练轮机手战列"): re.compile("航战耐久.{1,3}10"),
    ("航战耐久", 1, "轮机手战列"): re.compile("航战耐久.{1,3}75"),
    ("巡洋耐久", 3, "轮机长巡洋"): re.compile("超巡耐久.{1,3}10"),
    ("巡洋耐久", 2, "熟练轮机手巡洋"): re.compile("超巡耐久.{1,3}70"),
    ("巡洋耐久", 1, "轮机手巡洋"): re.compile("超巡耐久.{1,3}50"),
    ("驱逐耐久", 3, "轮机长驱逐"): re.compile("驱逐耐久.{1,3}60"),
    ("驱逐耐久", 2, "熟练轮机手驱逐"): re.compile("驱逐耐久.{1,3}42"),
    ("驱逐耐久", 1, "轮机手驱逐"): re.compile("驱逐耐久.{1,3}30"),
    ("潜艇耐久", 3, "轮机长潜艇"): re.compile("潜母耐久.{1,3}50"),
    ("潜艇耐久", 2, "熟练轮机手潜艇"): re.compile("潜母耐久.{1,3}35"),
    ("潜艇耐久", 1, "轮机手潜艇"): re.compile("潜母耐久.{1,3}25"),
    ("运输装填", 3, "无影手特殊"): re.compile("运输装填.{1,3}6"),
    ("运输装填", 2, "熟练装填手特殊"): re.compile("运输装填.{1,3}4"),
    ("运输装填", 1, "装填新手特殊"): re.compile("运输装填.{1,3}3"),
    ("航母装填", 3, "格纳库之主"): re.compile("正航装填.{1,3}6"),
    ("航母装填", 2, "熟练技师"): re.compile("正航装填.{1,3}4"),
    ("航母装填", 1, "新手整备士"): re.compile("正航装填.{1,3}3"),
    ("航战装填", 3, "无影手战列"): re.compile("航战装填.{1,3}6"),
    ("航战装填", 2, "熟练装填手战列"): re.compile("航战装填.{1,3}4"),
    ("航战装填", 1, "装填新手战列"): re.compile("航战装填.{1,3}3"),
    ("巡洋装填", 3, "无影手巡洋"): re.compile("超巡装填.{1,3}8"),
    ("巡洋装填", 2, "熟练装填手巡洋"): re.compile("超巡装填.{1,3}5"),
    ("巡洋装填", 1, "装填新手巡洋"): re.compile("超巡装填.{1,3}4"),
    ("驱逐装填", 3, "无影手驱逐"): re.compile("驱逐装填.{1,3}10"),
    ("驱逐装填", 2, "熟练装填手驱逐"): re.compile("驱逐装填.{1,3}7"),
    ("驱逐装填", 1, "装填新手驱逐"): re.compile("驱逐装填.{1,3}5"),
    ("潜艇装填", 3, "无影手潜艇"): re.compile("潜母装填.{1,3}6"),
    ("潜艇装填", 2, "熟练装填手潜艇"): re.compile("潜母装填.{1,3}4"),
    ("潜艇装填", 1, "装填新手潜艇"): re.compile("潜母装填.{1,3}3"),
    ("主力反潜", 3, "人形声纳主力"): re.compile("主力反潜.{1,3}6"),
    ("主力反潜", 2, "熟练声纳兵主力"): re.compile("主力反潜.{1,3}4"),
    ("主力反潜", 1, "声纳兵主力"): re.compile("主力反潜.{1,3}3"),
    ("先锋反潜", 3, "人形声纳先锋"): re.compile("先锋反潜.{1,3}8"),
    ("先锋反潜", 2, "熟练声纳兵先锋"): re.compile("先锋反潜.{1,3}5"),
    ("先锋反潜", 1, "声纳兵先锋"): re.compile("先锋反潜.{1,3}4"),
    ("主力防空", 3, "敌机克星主力"): re.compile("主力防空.{1,3}20"),
    ("主力防空", 2, "熟练对空炮手主力"): re.compile("主力防空.{1,3}14"),
    ("主力防空", 1, "对空炮手主力"): re.compile("主力防空.{1,3}10"),
    ("先锋防空", 3, "敌机克星先锋"): re.compile("先锋防空.{1,3}16"),
    ("先锋防空", 2, "熟练对空炮手先锋"): re.compile("先锋防空.{1,3}11"),
    ("先锋防空", 1, "对空炮手先锋"): re.compile("先锋防空.{1,3}8"),
    ("航战航空", 3, "空中杀手特殊"): re.compile("航战航空.{1,3}10"),
    ("航战航空", 2, "熟练机师特殊"): re.compile("航战航空.{1,3}7"),
    ("航战航空", 1, "航空新兵特殊"): re.compile("航战航空.{1,3}5"),
    ("航母航空", 3, "空中杀手空母"): re.compile("正航航空.{1,3}20"),
    ("航母航空", 2, "熟练机师空母"): re.compile("正航航空.{1,3}14"),
    ("航母航空", 1, "航空新兵空母"): re.compile("正航航空.{1,3}10"),
    ("重巡雷击", 3, "雷击长巡洋"): re.compile("重巡雷击.{1,3}12"),
    ("重巡雷击", 2, "熟练雷击士巡洋"): re.compile("重巡雷击.{1,3}8"),
    ("重巡雷击", 1, "新人雷击士巡洋"): re.compile("重巡雷击.{1,3}6"),
    ("驱逐雷击", 3, "雷击长驱逐"): re.compile("驱逐雷击.{1,3}20"),
    ("驱逐雷击", 2, "熟练雷击士驱逐"): re.compile("驱逐雷击.{1,3}14"),
    ("驱逐雷击", 1, "新人雷击士驱逐"): re.compile("驱逐雷击.{1,3}10"),
    ("潜艇雷击", 3, "雷击长潜艇"): re.compile("潜母雷击.{1,3}20"),
    ("潜艇雷击", 2, "熟练雷击士潜艇"): re.compile("潜母雷击.{1,3}14"),
    ("潜艇雷击", 1, "新人雷击士潜艇"): re.compile("潜母雷击.{1,3}10"),
    ("战列炮击", 3, "炮术长主力"): re.compile("重炮炮击.{1,3}16"),
    ("战列炮击", 2, "熟练炮手主力"): re.compile("重炮炮击.{1,3}11"),
    ("战列炮击", 1, "炮击新手主力"): re.compile("重炮炮击.{1,3}8"),
    ("巡洋炮击", 3, "炮术长巡洋"): re.compile("超巡炮击.{1,3}10"),
    ("巡洋炮击", 2, "熟练炮手巡洋"): re.compile("超巡炮击.{1,3}7"),
    ("巡洋炮击", 1, "炮击新手巡洋"): re.compile("超巡炮击.{1,3}5"),
    ("驱逐炮击", 3, "炮术长驱逐"): re.compile("驱逐炮击.{1,3}6"),
    ("驱逐炮击", 2, "熟练炮手驱逐"): re.compile("驱逐炮击.{1,3}4"),
    ("驱逐炮击", 1, "炮击新手驱逐"): re.compile("驱逐炮击.{1,3}3"),
}
