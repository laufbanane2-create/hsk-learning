#!/usr/bin/env python3
"""Build a German-language Anki deck for the 150-word HSK 2.0 vocabulary.

Usage:
    python3 generate_hsk2_deck.py
    python3 generate_hsk2_deck.py --output /path/to/HSK2_DualTask_Deck.apkg

The script is self-contained apart from genanki.  It embeds the repository's
pre-generated sentence MP3s, so listening prompts never depend on Anki TTS.
"""

import argparse
import json
import re
import sqlite3
import zipfile
from pathlib import Path

import genanki


MODEL_ID = 1607392388
DECK_ID = 2059384721
DECK_NAME = "HSK 2 - Offizieller Wortschatz (Hör- & Leseverstehen)"
OUTPUT_FILE = "HSK2_DualTask_Deck.apkg"
SCRIPT_DIR = Path(__file__).resolve().parent
AUDIO_DIR = SCRIPT_DIR / "audio"
PINYIN_VALUE_PATTERN = re.compile(r"^[A-Za-zÀ-ɏ ，。！？、]+$")

# The order is the official HSK 2.0 list of 150 additions to HSK 1.  Every
# vocabulary row is ultimately expanded with a hard-coded pinyin transcription
# of its audio sentence below.
OFFICIAL_HSK2_WORDS = (
    "吧", "白", "百", "帮助", "报纸", "比", "别", "宾馆", "长", "唱歌",
    "出", "穿", "次", "从", "错", "打篮球", "大家", "到", "得", "等",
    "弟弟", "第一", "懂", "对", "房间", "非常", "服务员", "高", "告诉", "哥哥",
    "给", "公共汽车", "公司", "贵", "过", "还", "孩子", "好吃", "黑", "红",
    "火车站", "机场", "鸡蛋", "件", "教室", "姐姐", "介绍", "近", "进", "就",
    "觉得", "咖啡", "开始", "考试", "可能", "可以", "课", "快", "快乐", "累",
    "离", "两", "零", "路", "旅游", "卖", "慢", "忙", "每", "妹妹",
    "门", "面条", "男", "您", "牛奶", "女", "旁边", "跑步", "便宜", "票",
    "妻子", "起床", "千", "铅笔", "晴", "去年", "让", "日", "上班", "身体",
    "生病", "生日", "时间", "事情", "手表", "手机", "说话", "送", "虽然……但是……", "它",
    "踢足球", "题", "跳舞", "外", "完", "玩", "晚上", "往", "为什么", "问",
    "问题", "西瓜", "希望", "洗", "小时", "笑", "新", "姓", "休息", "雪",
    "颜色", "眼睛", "羊肉", "要", "药", "也", "一下", "已经", "一起", "意思",
    "阴", "因为……所以……", "游泳", "右边", "鱼", "远", "运动", "再", "早上", "丈夫",
    "找", "着", "真", "正在", "只", "知道", "准备", "走", "最", "左边",
)


HSK2_VOCAB = [
    ("hsk2_ba", "吧", "ba", "Vorschlagspartikel",
     "我们去看电影吧。", "Lasst uns ins Kino gehen.",
     "我们现在回家吧。", "Gehen wir jetzt nach Hause.", "hsk2_ba.mp3"),
    ("hsk2_bai", "白", "bái", "weiß",
     "她穿了一件白衬衫。", "Sie trägt ein weißes Hemd.",
     "桌子上有一张白纸。", "Auf dem Tisch liegt ein weißes Blatt Papier.", "hsk2_bai.mp3"),
    ("hsk2_bai2", "百", "bǎi", "hundert",
     "这本书一百页。", "Dieses Buch hat hundert Seiten.",
     "这里有两百个人。", "Hier sind zweihundert Menschen.", "hsk2_bai2.mp3"),
    ("hsk2_bangzhu", "帮助", "bāngzhù", "helfen; Hilfe",
     "谢谢你帮助我。", "Danke, dass du mir hilfst.",
     "老师常常帮助学生。", "Die Lehrerin hilft den Schülern oft.", "hsk2_bangzhu.mp3"),
    ("hsk2_baozhi", "报纸", "bàozhǐ", "Zeitung",
     "我爸爸每天早上看报纸。", "Mein Vater liest jeden Morgen Zeitung.",
     "这份报纸是今天的。", "Diese Zeitung ist von heute.", "hsk2_baozhi.mp3"),
    ("hsk2_bi", "比", "bǐ", "vergleichen; als",
     "今天比昨天冷。", "Heute ist es kälter als gestern.",
     "我比弟弟高。", "Ich bin größer als mein jüngerer Bruder.", "hsk2_bi.mp3"),
    ("hsk2_bie", "别", "bié", "nicht; lass das",
     "别忘了带水。", "Vergiss nicht, Wasser mitzunehmen.",
     "别在这里说话。", "Sprich hier nicht.", "hsk2_bie.mp3"),
    ("hsk2_binguan", "宾馆", "bīnguǎn", "Hotel",
     "我住在一家宾馆里。", "Ich wohne in einem Hotel.",
     "这家宾馆离机场很近。", "Dieses Hotel ist nahe am Flughafen.", "hsk2_binguan.mp3"),
    ("hsk2_chang", "长", "cháng", "lang",
     "这条路很长，要走很久。", "Diese Straße ist sehr lang; man muss lange laufen.",
     "她的头发很长。", "Ihr Haar ist sehr lang.", "hsk2_chang.mp3"),
    ("hsk2_changge", "唱歌", "chàng gē", "singen",
     "她很喜欢唱歌。", "Sie singt sehr gern.",
     "我们一起唱歌吧。", "Lasst uns zusammen singen.", "hsk2_changge.mp3"),
    ("hsk2_chu", "出", "chū", "hinausgehen; heraus",
     "他出去了。", "Er ist hinausgegangen.",
     "请从这个门出去。", "Bitte geh durch diese Tür hinaus.", "hsk2_chu.mp3"),
    ("hsk2_chuan", "穿", "chuān", "tragen; anziehen",
     "今天很冷，多穿衣服。", "Heute ist es kalt, zieh mehr Kleidung an.",
     "他每天穿蓝色的衣服。", "Er trägt jeden Tag blaue Kleidung.", "hsk2_chuan.mp3"),
    ("hsk2_ci", "次", "cì", "Mal",
     "我去过北京两次。", "Ich war zweimal in Peking.",
     "这是我第一次来中国。", "Das ist mein erstes Mal in China.", "hsk2_ci.mp3"),
    ("hsk2_cong", "从", "cóng", "von; aus",
     "我从北京来。", "Ich komme aus Peking.",
     "请从这里开始读。", "Bitte beginne hier zu lesen.", "hsk2_cong.mp3"),
    ("hsk2_cuo", "错", "cuò", "falsch; Fehler",
     "对不起，我说错了。", "Entschuldigung, ich habe es falsch gesagt.",
     "这个答案错了。", "Diese Antwort ist falsch.", "hsk2_cuo.mp3"),
    ("hsk2_dalanqiu", "打篮球", "dǎ lánqiú", "Basketball spielen",
     "他们喜欢打篮球。", "Sie spielen gern Basketball.",
     "下午我们去打篮球。", "Am Nachmittag spielen wir Basketball.", "hsk2_dalanqiu.mp3"),
    ("hsk2_dajia", "大家", "dàjiā", "alle; alle zusammen",
     "大家好，我叫李明。", "Hallo zusammen, ich heiße Li Ming.",
     "大家都在教室里。", "Alle sind im Klassenzimmer.", "hsk2_dajia.mp3"),
    ("hsk2_dao", "到", "dào", "ankommen; bis",
     "我到学校了。", "Ich bin in der Schule angekommen.",
     "请你八点到公司。", "Bitte komm um acht Uhr zur Firma.", "hsk2_dao.mp3"),
    ("hsk2_de2", "得", "de", "Strukturpartikel",
     "他说得很好。", "Er spricht sehr gut.",
     "你跑得太快了。", "Du läufst zu schnell.", "hsk2_de2.mp3"),
    ("hsk2_deng", "等", "děng", "warten",
     "请等一下。", "Bitte warte einen Moment.",
     "我在门口等你。", "Ich warte an der Tür auf dich.", "hsk2_deng.mp3"),
    ("hsk2_didi", "弟弟", "dìdi", "jüngerer Bruder",
     "我弟弟是学生。", "Mein jüngerer Bruder ist Schüler.",
     "弟弟今年十岁。", "Mein jüngerer Bruder ist dieses Jahr zehn Jahre alt.", "hsk2_didi.mp3"),
    ("hsk2_diyi", "第一", "dì yī", "erste; Nummer eins",
     "他是班里第一名。", "Er ist der Beste in der Klasse.",
     "今天是我第一天上班。", "Heute ist mein erster Arbeitstag.", "hsk2_diyi.mp3"),
    ("hsk2_dong2", "懂", "dǒng", "verstehen",
     "你懂我说的意思吗？", "Verstehst du, was ich meine?",
     "这本书我看不懂。", "Ich verstehe dieses Buch nicht.", "hsk2_dong2.mp3"),
    ("hsk2_dui", "对", "duì", "richtig; recht",
     "你说的对。", "Was du sagst, ist richtig.",
     "这个地方对吗？", "Ist dieser Ort richtig?", "hsk2_dui.mp3"),
    ("hsk2_fangjian", "房间", "fángjiān", "Zimmer",
     "我的房间很小。", "Mein Zimmer ist sehr klein.",
     "请进我的房间。", "Bitte komm in mein Zimmer.", "hsk2_fangjian.mp3"),
    ("hsk2_feichang", "非常", "fēicháng", "sehr; äußerst",
     "这部电影非常精彩。", "Dieser Film ist äußerst spannend.",
     "我非常喜欢这本书。", "Ich mag dieses Buch sehr.", "hsk2_feichang.mp3"),
    ("hsk2_fuwuyuan", "服务员", "fúwùyuán", "Bedienung",
     "服务员，请给我一杯水。", "Bedienung, bitte geben Sie mir ein Glas Wasser.",
     "服务员正在拿菜单。", "Die Bedienung bringt gerade die Speisekarte.", "hsk2_fuwuyuan.mp3"),
    ("hsk2_gao", "高", "gāo", "hoch; groß",
     "他很高。", "Er ist groß.",
     "这个桌子太高了。", "Dieser Tisch ist zu hoch.", "hsk2_gao.mp3"),
    ("hsk2_gaosu", "告诉", "gàosu", "sagen; mitteilen",
     "请告诉我你的名字。", "Bitte sag mir deinen Namen.",
     "妈妈告诉我一个事情。", "Mama erzählt mir eine Sache.", "hsk2_gaosu.mp3"),
    ("hsk2_gege", "哥哥", "gēge", "älterer Bruder",
     "我哥哥很好。", "Mein älterer Bruder ist sehr nett.",
     "哥哥在公司上班。", "Mein älterer Bruder arbeitet in einer Firma.", "hsk2_gege.mp3"),
    ("hsk2_gei", "给", "gěi", "geben; für; an",
     "妈妈给我买了一个礼物。", "Mama hat mir ein Geschenk gekauft.",
     "请给老师这本书。", "Bitte gib der Lehrerin dieses Buch.", "hsk2_gei.mp3"),
    ("hsk2_gonggongqiche", "公共汽车", "gōnggòng qìchē", "Bus",
     "我坐公共汽车去学校。", "Ich fahre mit dem Bus zur Schule.",
     "公共汽车马上就来。", "Der Bus kommt gleich.", "hsk2_gonggongqiche.mp3"),
    ("hsk2_gongsi", "公司", "gōngsī", "Firma",
     "他在一家大公司工作。", "Er arbeitet in einer großen Firma.",
     "我家离公司不远。", "Mein Zuhause ist nicht weit von der Firma entfernt.", "hsk2_gongsi.mp3"),
    ("hsk2_gui", "贵", "guì", "teuer",
     "这件衣服很贵，我买不起。", "Dieses Kleidungsstück ist sehr teuer; ich kann es nicht kaufen.",
     "这个苹果不贵。", "Dieser Apfel ist nicht teuer.", "hsk2_gui.mp3"),
    ("hsk2_guo", "过", "guò", "schon einmal; Erfahrungsaspekt",
     "我去过北京。", "Ich war schon einmal in Peking.",
     "你看过这个电影吗？", "Hast du diesen Film schon gesehen?", "hsk2_guo.mp3"),
    ("hsk2_hai", "还", "hái", "noch; auch",
     "他还在学校。", "Er ist noch in der Schule.",
     "我还想喝一杯茶。", "Ich möchte noch eine Tasse Tee trinken.", "hsk2_hai.mp3"),
    ("hsk2_haizi", "孩子", "háizi", "Kind",
     "这个孩子很聪明。", "Dieses Kind ist sehr klug.",
     "孩子在外面玩。", "Das Kind spielt draußen.", "hsk2_haizi.mp3"),
    ("hsk2_haochi", "好吃", "hǎochī", "lecker",
     "这道菜非常好吃！", "Dieses Gericht ist sehr lecker!",
     "这家店的面条很好吃。", "Die Nudeln in diesem Laden sind sehr lecker.", "hsk2_haochi.mp3"),
    ("hsk2_hei", "黑", "hēi", "schwarz",
     "他有一只黑猫。", "Er hat eine schwarze Katze.",
     "我的书包是黑的。", "Mein Rucksack ist schwarz.", "hsk2_hei.mp3"),
    ("hsk2_hong", "红", "hóng", "rot",
     "这是红色的。", "Das ist rot.",
     "她喜欢红花。", "Sie mag rote Blumen.", "hsk2_hong.mp3"),
    ("hsk2_huochezhan", "火车站", "huǒchēzhàn", "Bahnhof",
     "火车站在哪里？", "Wo ist der Bahnhof?",
     "我们在火车站见。", "Wir treffen uns am Bahnhof.", "hsk2_huochezhan.mp3"),
    ("hsk2_jichang", "机场", "jīchǎng", "Flughafen",
     "我去机场接朋友。", "Ich fahre zum Flughafen, um einen Freund abzuholen.",
     "机场离这里很远。", "Der Flughafen ist weit von hier entfernt.", "hsk2_jichang.mp3"),
    ("hsk2_jidan", "鸡蛋", "jīdàn", "Ei",
     "我吃一个鸡蛋。", "Ich esse ein Ei.",
     "冰箱里有鸡蛋吗？", "Sind Eier im Kühlschrank?", "hsk2_jidan.mp3"),
    ("hsk2_jian", "件", "jiàn", "Zählwort für Kleidung und Angelegenheiten",
     "我买了两件衣服。", "Ich habe zwei Kleidungsstücke gekauft.",
     "这是一件重要的事情。", "Das ist eine wichtige Angelegenheit.", "hsk2_jian.mp3"),
    ("hsk2_jiaoshi", "教室", "jiàoshì", "Klassenzimmer",
     "教室很大。", "Das Klassenzimmer ist groß.",
     "学生都在教室学习。", "Die Schüler lernen alle im Klassenzimmer.", "hsk2_jiaoshi.mp3"),
    ("hsk2_jiejie", "姐姐", "jiějie", "ältere Schwester",
     "我姐姐是老师。", "Meine ältere Schwester ist Lehrerin.",
     "姐姐喜欢喝咖啡。", "Meine ältere Schwester trinkt gern Kaffee.", "hsk2_jiejie.mp3"),
    ("hsk2_jieshao", "介绍", "jièshào", "vorstellen; Einführung",
     "我介绍一下。", "Ich stelle mich kurz vor.",
     "请介绍你的朋友。", "Bitte stell deinen Freund vor.", "hsk2_jieshao.mp3"),
    ("hsk2_jin2", "近", "jìn", "nah",
     "我家很近。", "Mein Zuhause ist nah.",
     "超市就在学校附近。", "Der Supermarkt ist ganz in der Nähe der Schule.", "hsk2_jin2.mp3"),
    ("hsk2_jin", "进", "jìn", "eintreten; hineingehen",
     "请进。", "Bitte komm herein.",
     "不要进这个房间。", "Geh nicht in dieses Zimmer.", "hsk2_jin.mp3"),
    ("hsk2_jiu", "就", "jiù", "dann; gleich",
     "我马上就来。", "Ich komme sofort.",
     "他一回家就睡觉。", "Sobald er nach Hause kommt, schläft er.", "hsk2_jiu.mp3"),
    ("hsk2_juede", "觉得", "juéde", "finden; denken",
     "我觉得今天很冷。", "Ich finde, dass es heute sehr kalt ist.",
     "你觉得这个怎么样？", "Wie findest du das?", "hsk2_juede.mp3"),
    ("hsk2_kafei", "咖啡", "kāfēi", "Kaffee",
     "我喜欢喝咖啡。", "Ich trinke gern Kaffee.",
     "早上我不喝咖啡。", "Morgens trinke ich keinen Kaffee.", "hsk2_kafei.mp3"),
    ("hsk2_kaishi", "开始", "kāishǐ", "anfangen; beginnen",
     "我们开始学习吧。", "Lasst uns anfangen zu lernen.",
     "电影八点开始。", "Der Film beginnt um acht Uhr.", "hsk2_kaishi.mp3"),
    ("hsk2_kaoshi", "考试", "kǎoshì", "Prüfung",
     "下周我有一个重要的考试。", "Nächste Woche habe ich eine wichtige Prüfung.",
     "明天我们考试。", "Morgen haben wir eine Prüfung.", "hsk2_kaoshi.mp3"),
    ("hsk2_keneng", "可能", "kěnéng", "vielleicht; möglich",
     "他可能今天不来了。", "Vielleicht kommt er heute nicht.",
     "明天可能下雨。", "Morgen regnet es vielleicht.", "hsk2_keneng.mp3"),
    ("hsk2_keyi", "可以", "kěyǐ", "können; dürfen",
     "我可以问你一个问题吗？", "Darf ich dir eine Frage stellen?",
     "这里可以坐吗？", "Darf man hier sitzen?", "hsk2_keyi.mp3"),
    ("hsk2_ke3", "课", "kè", "Unterricht; Lektion",
     "我上午有三节课。", "Ich habe am Vormittag drei Unterrichtsstunden.",
     "汉语课几点开始？", "Wann beginnt der Chinesischunterricht?", "hsk2_ke3.mp3"),
    ("hsk2_kuai2", "快", "kuài", "schnell",
     "他走路很快。", "Er geht schnell.",
     "请快一点，我们要迟到了。", "Bitte beeil dich, wir kommen zu spät.", "hsk2_kuai2.mp3"),
    ("hsk2_kuaile", "快乐", "kuàilè", "glücklich",
     "祝你快乐！", "Ich wünsche dir Glück!",
     "孩子们玩得很快乐。", "Die Kinder spielen fröhlich.", "hsk2_kuaile.mp3"),
    ("hsk2_lei", "累", "lèi", "müde",
     "我今天很累。", "Ich bin heute sehr müde.",
     "跑步以后他很累。", "Nach dem Laufen ist er sehr müde.", "hsk2_lei.mp3"),
    ("hsk2_li", "离", "lí", "entfernt von",
     "学校离我家很近。", "Die Schule ist nahe bei meinem Zuhause.",
     "北京离上海很远。", "Peking ist weit von Shanghai entfernt.", "hsk2_li.mp3"),
    ("hsk2_liang", "两", "liǎng", "zwei",
     "我有两本书。", "Ich habe zwei Bücher.",
     "请给我两杯水。", "Bitte gib mir zwei Gläser Wasser.", "hsk2_liang.mp3"),
    ("hsk2_ling", "零", "líng", "null",
     "现在是零点。", "Es ist jetzt null Uhr.",
     "这个号码最后是零。", "Diese Nummer endet mit einer Null.", "hsk2_ling.mp3"),
    ("hsk2_lu", "路", "lù", "Straße; Weg",
     "这条路很长。", "Diese Straße ist sehr lang.",
     "请告诉我去学校的路。", "Bitte sag mir den Weg zur Schule.", "hsk2_lu.mp3"),
    ("hsk2_luyou", "旅游", "lǚyóu", "reisen; Tourismus",
     "我喜欢旅游，看新地方。", "Ich reise gern und sehe neue Orte.",
     "去年我们去中国旅游。", "Letztes Jahr sind wir nach China gereist.", "hsk2_luyou.mp3"),
    ("hsk2_mai", "卖", "mài", "verkaufen",
     "这家店卖新鲜水果。", "Dieser Laden verkauft frisches Obst.",
     "他们卖咖啡和茶。", "Sie verkaufen Kaffee und Tee.", "hsk2_mai.mp3"),
    ("hsk2_man", "慢", "màn", "langsam",
     "请说慢一点，我听不清楚。", "Bitte sprich etwas langsamer, ich höre nicht klar.",
     "这辆车走得很慢。", "Dieses Auto fährt sehr langsam.", "hsk2_man.mp3"),
    ("hsk2_mang", "忙", "máng", "beschäftigt",
     "我今天很忙。", "Ich bin heute sehr beschäftigt.",
     "妈妈下午不忙。", "Mama ist am Nachmittag nicht beschäftigt.", "hsk2_mang.mp3"),
    ("hsk2_mei", "每", "měi", "jeder; jeden",
     "我每天学习。", "Ich lerne jeden Tag.",
     "每个学生都有一本书。", "Jeder Schüler hat ein Buch.", "hsk2_mei.mp3"),
    ("hsk2_meimei", "妹妹", "mèimei", "jüngere Schwester",
     "我妹妹很可爱。", "Meine jüngere Schwester ist sehr lieb.",
     "妹妹在学校学习汉语。", "Meine jüngere Schwester lernt in der Schule Chinesisch.", "hsk2_meimei.mp3"),
    ("hsk2_men", "门", "mén", "Tür",
     "请开门。", "Bitte öffne die Tür.",
     "门在房间的右边。", "Die Tür ist auf der rechten Seite des Zimmers.", "hsk2_men.mp3"),
    ("hsk2_miantiao", "面条", "miàntiáo", "Nudeln",
     "我最喜欢吃面条。", "Ich esse am liebsten Nudeln.",
     "这碗面条很好吃。", "Diese Schüssel Nudeln ist sehr lecker.", "hsk2_miantiao.mp3"),
    ("hsk2_nan3", "男", "nán", "männlich; Mann",
     "他是男老师。", "Er ist ein männlicher Lehrer.",
     "那个男学生是我哥哥。", "Dieser männliche Schüler ist mein älterer Bruder.", "hsk2_nan3.mp3"),
    ("hsk2_nin", "您", "nín", "Sie (höflich)",
     "您好！", "Guten Tag!",
     "您想喝茶吗？", "Möchten Sie Tee trinken?", "hsk2_nin.mp3"),
    ("hsk2_niunai", "牛奶", "niúnǎi", "Milch",
     "我每天喝牛奶。", "Ich trinke jeden Tag Milch.",
     "请给孩子一杯牛奶。", "Bitte gib dem Kind ein Glas Milch.", "hsk2_niunai.mp3"),
    ("hsk2_nv", "女", "nǚ", "weiblich; Frau",
     "她是女老师。", "Sie ist eine Lehrerin.",
     "那个女学生是我姐姐。", "Diese Schülerin ist meine ältere Schwester.", "hsk2_nv.mp3"),
    ("hsk2_pangbian", "旁边", "pángbiān", "neben; daneben",
     "学校在医院旁边。", "Die Schule liegt neben dem Krankenhaus.",
     "请坐在我旁边。", "Bitte setz dich neben mich.", "hsk2_pangbian.mp3"),
    ("hsk2_paobu", "跑步", "pǎobù", "laufen; joggen",
     "我每天早上跑步半个小时。", "Ich jogge jeden Morgen eine halbe Stunde.",
     "他喜欢在公园跑步。", "Er läuft gern im Park.", "hsk2_paobu.mp3"),
    ("hsk2_pianyi", "便宜", "piányí", "billig; günstig",
     "这家店的东西很便宜。", "Die Dinge in diesem Laden sind sehr günstig.",
     "这个房间不便宜。", "Dieses Zimmer ist nicht billig.", "hsk2_pianyi.mp3"),
    ("hsk2_piao", "票", "piào", "Fahrkarte; Eintrittskarte",
     "我买了两张电影票。", "Ich habe zwei Kinokarten gekauft.",
     "你的火车票在哪里？", "Wo ist deine Fahrkarte?", "hsk2_piao.mp3"),
    ("hsk2_qizi", "妻子", "qīzi", "Ehefrau",
     "她是我的妻子。", "Sie ist meine Ehefrau.",
     "他的妻子在家。", "Seine Ehefrau ist zu Hause.", "hsk2_qizi.mp3"),
    ("hsk2_qichuang", "起床", "qǐchuáng", "aufstehen",
     "我七点起床。", "Ich stehe um sieben Uhr auf.",
     "孩子每天早上六点起床。", "Das Kind steht jeden Morgen um sechs Uhr auf.", "hsk2_qichuang.mp3"),
    ("hsk2_qian2", "千", "qiān", "tausend",
     "这里有一千个人。", "Hier sind tausend Menschen.",
     "这本书有一千页。", "Dieses Buch hat tausend Seiten.", "hsk2_qian2.mp3"),
    ("hsk2_qianbi", "铅笔", "qiānbǐ", "Bleistift",
     "这是我的铅笔。", "Das ist mein Bleistift.",
     "请用铅笔写名字。", "Bitte schreib deinen Namen mit einem Bleistift.", "hsk2_qianbi.mp3"),
    ("hsk2_qing2", "晴", "qíng", "sonnig",
     "今天天气晴。", "Heute ist das Wetter sonnig.",
     "明天会是晴天吗？", "Wird es morgen sonnig sein?", "hsk2_qing2.mp3"),
    ("hsk2_qunian", "去年", "qùnián", "letztes Jahr",
     "我去年去了中国。", "Letztes Jahr bin ich nach China gefahren.",
     "去年冬天很冷。", "Letzten Winter war es sehr kalt.", "hsk2_qunian.mp3"),
    ("hsk2_rang", "让", "ràng", "lassen; erlauben",
     "请让我先说。", "Bitte lass mich zuerst sprechen.",
     "老师让我们读书。", "Die Lehrerin lässt uns lesen.", "hsk2_rang.mp3"),
    ("hsk2_ri", "日", "rì", "Tag; Datum",
     "今天是八日。", "Heute ist der achte Tag des Monats.",
     "我的生日是十月二日。", "Mein Geburtstag ist der zweite Oktober.", "hsk2_ri.mp3"),
    ("hsk2_shangban", "上班", "shàngbān", "zur Arbeit gehen",
     "我八点上班。", "Ich gehe um acht Uhr zur Arbeit.",
     "爸爸星期一不上班。", "Papa geht am Montag nicht zur Arbeit.", "hsk2_shangban.mp3"),
    ("hsk2_shenti", "身体", "shēntǐ", "Körper; Gesundheit",
     "身体健康最重要。", "Gesundheit ist am wichtigsten.",
     "运动对身体很好。", "Sport ist gut für den Körper.", "hsk2_shenti.mp3"),
    ("hsk2_shengbing", "生病", "shēngbìng", "krank werden; krank sein",
     "我昨天生病了，在家休息。", "Ich war gestern krank und habe mich zu Hause ausgeruht.",
     "他生病了，不能上班。", "Er ist krank und kann nicht arbeiten.", "hsk2_shengbing.mp3"),
    ("hsk2_shengri", "生日", "shēngrì", "Geburtstag",
     "今天是我的生日。", "Heute ist mein Geburtstag.",
     "祝你生日快乐！", "Alles Gute zum Geburtstag!", "hsk2_shengri.mp3"),
    ("hsk2_shijian", "时间", "shíjiān", "Zeit",
     "我没有时间看电视。", "Ich habe keine Zeit, fernzusehen.",
     "现在没有时间吃饭。", "Jetzt ist keine Zeit zum Essen.", "hsk2_shijian.mp3"),
    ("hsk2_shiqing", "事情", "shìqíng", "Sache; Angelegenheit",
     "有什么事情可以告诉我。", "Wenn etwas ist, kannst du es mir sagen.",
     "这件事情很重要。", "Diese Angelegenheit ist sehr wichtig.", "hsk2_shiqing.mp3"),
    ("hsk2_shoubiao", "手表", "shǒubiǎo", "Armbanduhr",
     "这是我的手表。", "Das ist meine Armbanduhr.",
     "你的手表很漂亮。", "Deine Armbanduhr ist sehr schön.", "hsk2_shoubiao.mp3"),
    ("hsk2_shouji", "手机", "shǒujī", "Handy",
     "我的手机没有电了。", "Mein Handy hat keinen Akku mehr.",
     "请用手机给我打电话。", "Bitte ruf mich mit dem Handy an.", "hsk2_shouji.mp3"),
    ("hsk2_shuohua", "说话", "shuōhuà", "sprechen; reden",
     "上课的时候不要说话。", "Sprich nicht während des Unterrichts.",
     "他正在跟老师说话。", "Er spricht gerade mit der Lehrerin.", "hsk2_shuohua.mp3"),
    ("hsk2_song", "送", "sòng", "schenken; bringen",
     "他送给我一本书。", "Er hat mir ein Buch geschenkt.",
     "我送朋友去机场。", "Ich bringe einen Freund zum Flughafen.", "hsk2_song.mp3"),
    ("hsk2_suiran_danshi", "虽然……但是……", "suīrán … dànshì …", "obwohl … aber …",
     "虽然下雨，但是我们还是去。", "Obwohl es regnet, gehen wir trotzdem.",
     "虽然很累，但是他还在学习。", "Obwohl er müde ist, lernt er noch.", "hsk2_suiran_danshi.mp3"),
    ("hsk2_ta3", "它", "tā", "es",
     "这只猫很可爱，它叫小白。", "Diese Katze ist sehr lieb; sie heißt Xiaobai.",
     "我的手机在这里，它很新。", "Mein Handy ist hier; es ist sehr neu.", "hsk2_ta3.mp3"),
    ("hsk2_tizuqiu", "踢足球", "tī zúqiú", "Fußball spielen",
     "他们每周末一起踢足球。", "Sie spielen jedes Wochenende zusammen Fußball.",
     "哥哥下午去踢足球。", "Mein älterer Bruder spielt am Nachmittag Fußball.", "hsk2_tizuqiu.mp3"),
    ("hsk2_ti", "题", "tí", "Aufgabe; Frage",
     "这道题很难。", "Diese Aufgabe ist schwierig.",
     "老师在问一个题。", "Die Lehrerin stellt eine Frage.", "hsk2_ti.mp3"),
    ("hsk2_tiaowu", "跳舞", "tiàowǔ", "tanzen",
     "她非常喜欢跳舞。", "Sie tanzt sehr gern.",
     "晚上我们一起跳舞吧。", "Lasst uns heute Abend zusammen tanzen.", "hsk2_tiaowu.mp3"),
    ("hsk2_wai", "外", "wài", "außen; draußen",
     "他在外面。", "Er ist draußen.",
     "外面很冷，请进来。", "Draußen ist es kalt, bitte komm herein.", "hsk2_wai.mp3"),
    ("hsk2_wan2", "完", "wán", "beenden; fertig",
     "我做完了。", "Ich bin fertig.",
     "请写完这个题。", "Bitte bearbeite diese Aufgabe zu Ende.", "hsk2_wan2.mp3"),
    ("hsk2_wan", "玩", "wán", "spielen",
     "孩子在玩。", "Das Kind spielt.",
     "我们去公园玩吧。", "Lasst uns im Park spielen.", "hsk2_wan.mp3"),
    ("hsk2_wanshang", "晚上", "wǎnshang", "Abend",
     "晚上见。", "Bis heute Abend.",
     "我晚上看书。", "Ich lese abends.", "hsk2_wanshang.mp3"),
    ("hsk2_wang", "往", "wǎng", "in Richtung",
     "请往前走。", "Bitte geh geradeaus.",
     "火车往北京开。", "Der Zug fährt in Richtung Peking.", "hsk2_wang.mp3"),
    ("hsk2_weishenme", "为什么", "wèishénme", "warum",
     "你为什么学习汉语？", "Warum lernst du Chinesisch?",
     "他为什么不来？", "Warum kommt er nicht?", "hsk2_weishenme.mp3"),
    ("hsk2_wen", "问", "wèn", "fragen",
     "我可以问你一个问题吗？", "Darf ich dir eine Frage stellen?",
     "请问老师这个题。", "Frag bitte die Lehrerin nach dieser Aufgabe.", "hsk2_wen.mp3"),
    ("hsk2_wenti", "问题", "wèntí", "Frage; Problem",
     "这道题有问题，我不会做。", "Mit dieser Aufgabe stimmt etwas nicht; ich kann sie nicht lösen.",
     "你有什么问题吗？", "Hast du Fragen?", "hsk2_wenti.mp3"),
    ("hsk2_xigua", "西瓜", "xīguā", "Wassermelone",
     "夏天吃西瓜很解渴。", "Wassermelone löscht im Sommer gut den Durst.",
     "这个西瓜很甜。", "Diese Wassermelone ist sehr süß.", "hsk2_xigua.mp3"),
    ("hsk2_xiwang", "希望", "xīwàng", "hoffen; Wunsch",
     "我希望你来。", "Ich hoffe, dass du kommst.",
     "希望明天天气好。", "Hoffentlich ist das Wetter morgen gut.", "hsk2_xiwang.mp3"),
    ("hsk2_xi", "洗", "xǐ", "waschen",
     "我每天早上洗脸。", "Ich wasche jeden Morgen mein Gesicht.",
     "请洗你的手。", "Bitte wasch deine Hände.", "hsk2_xi.mp3"),
    ("hsk2_xiaoshi", "小时", "xiǎoshí", "Stunde",
     "我每天学习两个小时汉语。", "Ich lerne jeden Tag zwei Stunden Chinesisch.",
     "从这里到机场要一个小时。", "Von hier zum Flughafen braucht man eine Stunde.", "hsk2_xiaoshi.mp3"),
    ("hsk2_xiao", "笑", "xiào", "lachen; lächeln",
     "他总是笑着说话。", "Er spricht immer mit einem Lächeln.",
     "听到这个故事，大家都笑了。", "Als alle diese Geschichte hörten, lachten sie.", "hsk2_xiao.mp3"),
    ("hsk2_xin", "新", "xīn", "neu",
     "我买了一本新书。", "Ich habe ein neues Buch gekauft.",
     "这是我的新手机。", "Das ist mein neues Handy.", "hsk2_xin.mp3"),
    ("hsk2_xing", "姓", "xìng", "Familienname",
     "你姓什么？", "Wie ist dein Familienname?",
     "我姓王，他姓李。", "Mein Familienname ist Wang, seiner ist Li.", "hsk2_xing.mp3"),
    ("hsk2_xiuxi", "休息", "xiūxi", "sich ausruhen; Pause",
     "你该休息了。", "Du solltest dich ausruhen.",
     "我们中午休息一个小时。", "Wir machen mittags eine Stunde Pause.", "hsk2_xiuxi.mp3"),
    ("hsk2_xue", "雪", "xuě", "Schnee",
     "今天下雪了。", "Heute schneit es.",
     "孩子喜欢在雪里玩。", "Kinder spielen gern im Schnee.", "hsk2_xue.mp3"),
    ("hsk2_yanse", "颜色", "yánsè", "Farbe",
     "你喜欢什么颜色？", "Welche Farbe magst du?",
     "这件衣服的颜色很好看。", "Die Farbe dieses Kleidungsstücks sieht schön aus.", "hsk2_yanse.mp3"),
    ("hsk2_yanjing", "眼睛", "yǎnjing", "Auge",
     "我的眼睛很大。", "Meine Augen sind groß.",
     "不要用手碰眼睛。", "Berühre deine Augen nicht mit den Händen.", "hsk2_yanjing.mp3"),
    ("hsk2_yangrou", "羊肉", "yángròu", "Lammfleisch",
     "我喜欢吃羊肉。", "Ich esse gern Lammfleisch.",
     "这家店的羊肉很好吃。", "Das Lammfleisch in diesem Laden ist sehr lecker.", "hsk2_yangrou.mp3"),
    ("hsk2_yao", "要", "yào", "wollen; brauchen",
     "我要一杯水。", "Ich möchte ein Glas Wasser.",
     "你要去学校吗？", "Willst du zur Schule gehen?", "hsk2_yao.mp3"),
    ("hsk2_yao2", "药", "yào", "Medizin",
     "请吃药。", "Bitte nimm die Medizin.",
     "这个药一天吃两次。", "Nimm diese Medizin zweimal am Tag.", "hsk2_yao2.mp3"),
    ("hsk2_ye", "也", "yě", "auch",
     "我也喜欢中国。", "Ich mag China auch.",
     "他也会说汉语。", "Er kann auch Chinesisch sprechen.", "hsk2_ye.mp3"),
    ("hsk2_yixia", "一下", "yīxià", "kurz; einmal",
     "请看一下。", "Bitte schau kurz.",
     "我想问你一下。", "Ich möchte dich kurz etwas fragen.", "hsk2_yixia.mp3"),
    ("hsk2_yijing", "已经", "yǐjīng", "schon; bereits",
     "他已经回家了。", "Er ist schon nach Hause gegangen.",
     "我已经吃过饭了。", "Ich habe schon gegessen.", "hsk2_yijing.mp3"),
    ("hsk2_yiqi", "一起", "yīqǐ", "zusammen",
     "我们一起去吃饭吧。", "Lasst uns zusammen essen gehen.",
     "我和姐姐一起学习。", "Meine ältere Schwester und ich lernen zusammen.", "hsk2_yiqi.mp3"),
    ("hsk2_yisi", "意思", "yìsi", "Bedeutung",
     "这是什么意思？", "Was bedeutet das?",
     "我不懂这个词的意思。", "Ich verstehe die Bedeutung dieses Wortes nicht.", "hsk2_yisi.mp3"),
    ("hsk2_yin", "阴", "yīn", "bedeckt",
     "今天是阴天。", "Heute ist es bewölkt.",
     "阴天的时候不热。", "An bewölkten Tagen ist es nicht heiß.", "hsk2_yin.mp3"),
    ("hsk2_yinwei_suoyi", "因为……所以……", "yīnwèi … suǒyǐ …", "weil … deshalb …",
     "因为下雨，所以我没有去。", "Weil es geregnet hat, bin ich nicht gegangen.",
     "因为很忙，所以他没来。", "Weil er sehr beschäftigt ist, ist er nicht gekommen.", "hsk2_yinwei_suoyi.mp3"),
    ("hsk2_youyong", "游泳", "yóuyǒng", "schwimmen",
     "我喜欢游泳。", "Ich schwimme gern.",
     "夏天我们去游泳。", "Im Sommer gehen wir schwimmen.", "hsk2_youyong.mp3"),
    ("hsk2_youbian", "右边", "yòubian", "rechte Seite",
     "商店在右边。", "Der Laden ist auf der rechten Seite.",
     "请坐在我的右边。", "Bitte setz dich rechts von mir.", "hsk2_youbian.mp3"),
    ("hsk2_yu", "鱼", "yú", "Fisch",
     "我喜欢吃鱼。", "Ich esse gern Fisch.",
     "今天的鱼很新鲜。", "Der Fisch heute ist sehr frisch.", "hsk2_yu.mp3"),
    ("hsk2_yuan", "远", "yuǎn", "weit",
     "学校很远。", "Die Schule ist weit weg.",
     "我家离这里不远。", "Mein Zuhause ist nicht weit von hier.", "hsk2_yuan.mp3"),
    ("hsk2_yundong", "运动", "yùndòng", "Sport; sich bewegen",
     "我喜欢运动。", "Ich treibe gern Sport.",
     "每天运动对身体好。", "Täglicher Sport ist gut für die Gesundheit.", "hsk2_yundong.mp3"),
    ("hsk2_zai2", "再", "zài", "wieder; noch einmal",
     "请再说一遍。", "Bitte sag es noch einmal.",
     "明天我们再见。", "Morgen sehen wir uns wieder.", "hsk2_zai2.mp3"),
    ("hsk2_zaoshang", "早上", "zǎoshang", "Morgen",
     "我早上去学校。", "Ich gehe morgens zur Schule.",
     "早上好，你吃饭了吗？", "Guten Morgen, hast du schon gegessen?", "hsk2_zaoshang.mp3"),
    ("hsk2_zhangfu", "丈夫", "zhàngfu", "Ehemann",
     "他是我的丈夫。", "Er ist mein Ehemann.",
     "她的丈夫在公司工作。", "Ihr Ehemann arbeitet in einer Firma.", "hsk2_zhangfu.mp3"),
    ("hsk2_zhao", "找", "zhǎo", "suchen; finden",
     "我在找我的钥匙。", "Ich suche meinen Schlüssel.",
     "你在找什么？", "Was suchst du?", "hsk2_zhao.mp3"),
    ("hsk2_zhe2", "着", "zhe", "Verlaufsaspektpartikel",
     "他看着我。", "Er schaut mich an.",
     "门开着，请进。", "Die Tür ist offen, bitte komm herein.", "hsk2_zhe2.mp3"),
    ("hsk2_zhen", "真", "zhēn", "wirklich; echt",
     "这个故事是真的吗？", "Ist diese Geschichte wahr?",
     "今天天气真好。", "Das Wetter ist heute wirklich schön.", "hsk2_zhen.mp3"),
    ("hsk2_zhengzai", "正在", "zhèngzài", "gerade; im Begriff sein",
     "他正在学习汉语。", "Er lernt gerade Chinesisch.",
     "妈妈正在做饭。", "Mama kocht gerade.", "hsk2_zhengzai.mp3"),
    ("hsk2_zhi", "只", "zhǐ", "nur",
     "我只喝水，不喝咖啡。", "Ich trinke nur Wasser, keinen Kaffee.",
     "这里只有一个人。", "Hier ist nur eine Person.", "hsk2_zhi.mp3"),
    ("hsk2_zhidao", "知道", "zhīdào", "wissen",
     "你知道他住在哪里吗？", "Weißt du, wo er wohnt?",
     "我不知道这个地方。", "Ich kenne diesen Ort nicht.", "hsk2_zhidao.mp3"),
    ("hsk2_zhunbei", "准备", "zhǔnbèi", "vorbereiten",
     "我在准备考试。", "Ich bereite mich auf eine Prüfung vor.",
     "请准备好你的书。", "Bitte bereite dein Buch vor.", "hsk2_zhunbei.mp3"),
    ("hsk2_zou", "走", "zǒu", "gehen; laufen",
     "我们走吧。", "Lass uns gehen.",
     "他每天走路去公司。", "Er geht jeden Tag zu Fuß zur Firma.", "hsk2_zou.mp3"),
    ("hsk2_zui", "最", "zuì", "am meisten; -ste",
     "这是最好的。", "Das ist das Beste.",
     "我最喜欢这个颜色。", "Diese Farbe mag ich am liebsten.", "hsk2_zui.mp3"),
    ("hsk2_zuobian", "左边", "zuǒbian", "linke Seite",
     "银行在左边。", "Die Bank ist auf der linken Seite.",
     "请坐在我的左边。", "Bitte setz dich links von mir.", "hsk2_zuobian.mp3"),
]


# These transcriptions are deliberately stored as data rather than generated at
# runtime so the deck has no transliteration dependency.
AUDIO_SENTENCE_PINYIN = {
    "hsk2_ba": "Wǒ men qù kàn diàn yǐng ba。",
    "hsk2_bai": "Tā chuān le yī jiàn bái chèn shān。",
    "hsk2_bai2": "Zhè běn shū yì bǎi yè。",
    "hsk2_bangzhu": "Xiè xiè nǐ bāng zhù wǒ。",
    "hsk2_baozhi": "Wǒ bà ba měi tiān zǎo shàng kàn bào zhǐ。",
    "hsk2_bi": "Jīn tiān bǐ zuó tiān lěng。",
    "hsk2_bie": "Bié wàng le dài shuǐ。",
    "hsk2_binguan": "Wǒ zhù zài yī jiā bīn guǎn lǐ。",
    "hsk2_chang": "Zhè tiáo lù hěn cháng，yào zǒu hěn jiǔ。",
    "hsk2_changge": "Tā hěn xǐ huān chàng gē。",
    "hsk2_chu": "Tā chū qù le。",
    "hsk2_chuan": "Jīn tiān hěn lěng，duō chuān yī fú。",
    "hsk2_ci": "Wǒ qù guò běi jīng liǎng cì。",
    "hsk2_cong": "Wǒ cóng běi jīng lái。",
    "hsk2_cuo": "Duì bù qǐ，wǒ shuō cuò le。",
    "hsk2_dalanqiu": "Tā men xǐ huān dǎ lán qiú。",
    "hsk2_dajia": "Dà jiā hǎo，wǒ jiào lǐ míng。",
    "hsk2_dao": "Wǒ dào xué xiào le。",
    "hsk2_de2": "Tā shuō de hěn hǎo。",
    "hsk2_deng": "Qǐng děng yí xià。",
    "hsk2_didi": "Wǒ dì di shì xué shēng。",
    "hsk2_diyi": "Tā shì bān lǐ dì yì míng。",
    "hsk2_dong2": "Nǐ dǒng wǒ shuō de yì si ma？",
    "hsk2_dui": "Nǐ shuō de duì。",
    "hsk2_fangjian": "Wǒ de fáng jiān hěn xiǎo。",
    "hsk2_feichang": "Zhè bù diàn yǐng fēi cháng jīng cǎi。",
    "hsk2_fuwuyuan": "Fú wù yuán，qǐng gěi wǒ yī bēi shuǐ。",
    "hsk2_gao": "Tā hěn gāo。",
    "hsk2_gaosu": "Qǐng gào sù wǒ nǐ de míng zì。",
    "hsk2_gege": "Wǒ gē ge hěn hǎo。",
    "hsk2_gei": "Mā ma gěi wǒ mǎi le yí gè lǐ wù。",
    "hsk2_gonggongqiche": "Wǒ zuò gōng gòng qì chē qù xué xiào。",
    "hsk2_gongsi": "Tā zài yī jiā dà gōng sī gōng zuò。",
    "hsk2_gui": "Zhè jiàn yī fú hěn guì，wǒ mǎi bù qǐ。",
    "hsk2_guo": "Wǒ qù guò běi jīng。",
    "hsk2_hai": "Tā hái zài xué xiào。",
    "hsk2_haizi": "Zhè ge hái zi hěn cōng míng。",
    "hsk2_haochi": "Zhè dào cài fēi cháng hǎo chī！",
    "hsk2_hei": "Tā yǒu yī zhī hēi māo。",
    "hsk2_hong": "Zhè shì hóng sè de。",
    "hsk2_huochezhan": "Huǒ chē zhàn zài nǎ lǐ？",
    "hsk2_jichang": "Wǒ qù jī chǎng jiē péng yǒu。",
    "hsk2_jidan": "Wǒ chī yí gè jī dàn。",
    "hsk2_jian": "Wǒ mǎi le liǎng jiàn yī fú。",
    "hsk2_jiaoshi": "Jiào shì hěn dà。",
    "hsk2_jiejie": "Wǒ jiě jie shì lǎo shī。",
    "hsk2_jieshao": "Wǒ jiè shào yī xià。",
    "hsk2_jin2": "Wǒ jiā hěn jìn。",
    "hsk2_jin": "Qǐng jìn。",
    "hsk2_jiu": "Wǒ mǎ shàng jiù lái。",
    "hsk2_juede": "Wǒ jué de jīn tiān hěn lěng。",
    "hsk2_kafei": "Wǒ xǐ huān hē kā fēi。",
    "hsk2_kaishi": "Wǒ men kāi shǐ xué xí ba。",
    "hsk2_kaoshi": "Xià zhōu wǒ yǒu yí gè zhòng yào de kǎo shì。",
    "hsk2_keneng": "Tā kě néng jīn tiān bù lái le。",
    "hsk2_keyi": "Wǒ kě yǐ wèn nǐ yí gè wèn tí ma？",
    "hsk2_ke3": "Wǒ shàng wǔ yǒu sān jié kè。",
    "hsk2_kuai2": "Tā zǒu lù hěn kuài。",
    "hsk2_kuaile": "Zhù nǐ kuài lè！",
    "hsk2_lei": "Wǒ jīn tiān hěn lèi。",
    "hsk2_li": "Xué xiào lí wǒ jiā hěn jìn。",
    "hsk2_liang": "Wǒ yǒu liǎng běn shū。",
    "hsk2_ling": "Xiàn zài shì líng diǎn。",
    "hsk2_lu": "Zhè tiáo lù hěn cháng。",
    "hsk2_luyou": "Wǒ xǐ huān lǚ yóu，kàn xīn dì fāng。",
    "hsk2_mai": "Zhè jiā diàn mài xīn xiān shuǐ guǒ。",
    "hsk2_man": "Qǐng shuō màn yì diǎn，wǒ tīng bù qīng chǔ。",
    "hsk2_mang": "Wǒ jīn tiān hěn máng。",
    "hsk2_mei": "Wǒ měi tiān xué xí。",
    "hsk2_meimei": "Wǒ mèi mei hěn kě ài。",
    "hsk2_men": "Qǐng kāi mén。",
    "hsk2_miantiao": "Wǒ zuì xǐ huān chī miàn tiáo。",
    "hsk2_nan3": "Tā shì nán lǎo shī。",
    "hsk2_nin": "Nín hǎo！",
    "hsk2_niunai": "Wǒ měi tiān hē niú nǎi。",
    "hsk2_nv": "Tā shì nǚ lǎo shī。",
    "hsk2_pangbian": "Xué xiào zài yī yuàn páng biān。",
    "hsk2_paobu": "Wǒ měi tiān zǎo shàng pǎo bù bàn gè xiǎo shí。",
    "hsk2_pianyi": "Zhè jiā diàn de dōng xi hěn pián yi。",
    "hsk2_piao": "Wǒ mǎi le liǎng zhāng diàn yǐng piào。",
    "hsk2_qizi": "Tā shì wǒ de qī zi。",
    "hsk2_qichuang": "Wǒ qī diǎn qǐ chuáng。",
    "hsk2_qian2": "Zhè lǐ yǒu yī qiān gè rén。",
    "hsk2_qianbi": "Zhè shì wǒ de qiān bǐ。",
    "hsk2_qing2": "Jīn tiān tiān qì qíng。",
    "hsk2_qunian": "Wǒ qù nián qù le zhōng guó。",
    "hsk2_rang": "Qǐng ràng wǒ xiān shuō。",
    "hsk2_ri": "Jīn tiān shì bā rì。",
    "hsk2_shangban": "Wǒ bā diǎn shàng bān。",
    "hsk2_shenti": "Shēn tǐ jiàn kāng zuì zhòng yào。",
    "hsk2_shengbing": "Wǒ zuó tiān shēng bìng le，zài jiā xiū xī。",
    "hsk2_shengri": "Jīn tiān shì wǒ de shēng rì。",
    "hsk2_shijian": "Wǒ méi yǒu shí jiān kàn diàn shì。",
    "hsk2_shiqing": "Yǒu shén me shì qíng kě yǐ gào sù wǒ。",
    "hsk2_shoubiao": "Zhè shì wǒ de shǒu biǎo。",
    "hsk2_shouji": "Wǒ de shǒu jī méi yǒu diàn le。",
    "hsk2_shuohua": "Shàng kè de shí hòu bú yào shuō huà。",
    "hsk2_song": "Tā sòng gěi wǒ yī běn shū。",
    "hsk2_suiran_danshi": "Suī rán xià yǔ，dàn shì wǒ men hái shì qù。",
    "hsk2_ta3": "Zhè zhī māo hěn kě ài，tā jiào xiǎo bái。",
    "hsk2_tizuqiu": "Tā men měi zhōu mò yì qǐ tī zú qiú。",
    "hsk2_ti": "Zhè dào tí hěn nán。",
    "hsk2_tiaowu": "Tā fēi cháng xǐ huān tiào wǔ。",
    "hsk2_wai": "Tā zài wài miàn。",
    "hsk2_wan2": "Wǒ zuò wán le。",
    "hsk2_wan": "Hái zi zài wán。",
    "hsk2_wanshang": "Wǎn shàng jiàn。",
    "hsk2_wang": "Qǐng wǎng qián zǒu。",
    "hsk2_weishenme": "Nǐ wèi shén me xué xí hàn yǔ？",
    "hsk2_wen": "Wǒ kě yǐ wèn nǐ yí gè wèn tí ma？",
    "hsk2_wenti": "Zhè dào tí yǒu wèn tí，wǒ bú huì zuò。",
    "hsk2_xigua": "Xià tiān chī xī guā hěn jiě kě。",
    "hsk2_xiwang": "Wǒ xī wàng nǐ lái。",
    "hsk2_xi": "Wǒ měi tiān zǎo shàng xǐ liǎn。",
    "hsk2_xiaoshi": "Wǒ měi tiān xué xí liǎng gè xiǎo shí hàn yǔ。",
    "hsk2_xiao": "Tā zǒng shì xiào zhe shuō huà。",
    "hsk2_xin": "Wǒ mǎi le yī běn xīn shū。",
    "hsk2_xing": "Nǐ xìng shén me？",
    "hsk2_xiuxi": "Nǐ gāi xiū xī le。",
    "hsk2_xue": "Jīn tiān xià xuě le。",
    "hsk2_yanse": "Nǐ xǐ huān shén me yán sè？",
    "hsk2_yanjing": "Wǒ de yǎn jīng hěn dà。",
    "hsk2_yangrou": "Wǒ xǐ huān chī yáng ròu。",
    "hsk2_yao": "Wǒ yào yī bēi shuǐ。",
    "hsk2_yao2": "Qǐng chī yào。",
    "hsk2_ye": "Wǒ yě xǐ huān zhōng guó。",
    "hsk2_yixia": "Qǐng kàn yī xià。",
    "hsk2_yijing": "Tā yǐ jīng huí jiā le。",
    "hsk2_yiqi": "Wǒ men yì qǐ qù chī fàn ba。",
    "hsk2_yisi": "Zhè shì shén me yì si？",
    "hsk2_yin": "Jīn tiān shì yīn tiān。",
    "hsk2_yinwei_suoyi": "Yīn wèi xià yǔ，suǒ yǐ wǒ méi yǒu qù。",
    "hsk2_youyong": "Wǒ xǐ huān yóu yǒng。",
    "hsk2_youbian": "Shāng diàn zài yòu biān。",
    "hsk2_yu": "Wǒ xǐ huān chī yú。",
    "hsk2_yuan": "Xué xiào hěn yuǎn。",
    "hsk2_yundong": "Wǒ xǐ huān yùn dòng。",
    "hsk2_zai2": "Qǐng zài shuō yī biàn。",
    "hsk2_zaoshang": "Wǒ zǎo shàng qù xué xiào。",
    "hsk2_zhangfu": "Tā shì wǒ de zhàng fū。",
    "hsk2_zhao": "Wǒ zài zhǎo wǒ de yào shi。",
    "hsk2_zhe2": "Tā kàn zhe wǒ。",
    "hsk2_zhen": "Zhè ge gù shì shì zhēn de ma？",
    "hsk2_zhengzai": "Tā zhèng zài xué xí hàn yǔ。",
    "hsk2_zhi": "Wǒ zhǐ hē shuǐ，bù hē kā fēi。",
    "hsk2_zhidao": "Nǐ zhī dào tā zhù zài nǎ lǐ ma？",
    "hsk2_zhunbei": "Wǒ zài zhǔn bèi kǎo shì。",
    "hsk2_zou": "Wǒ men zǒu ba。",
    "hsk2_zui": "Zhè shì zuì hǎo de。",
    "hsk2_zuobian": "Yín háng zài zuǒ biān。",
}

READING_SENTENCE_PINYIN = {
    "hsk2_ba": "Wǒ men xiàn zài huí jiā ba。",
    "hsk2_bai": "Zhuō zi shàng yǒu yì zhāng bái zhǐ。",
    "hsk2_bai2": "Zhè lǐ yǒu liǎng bǎi gè rén。",
    "hsk2_bangzhu": "Lǎo shī cháng cháng bāng zhù xué shēng。",
    "hsk2_baozhi": "Zhè fèn bào zhǐ shì jīn tiān de。",
    "hsk2_bi": "Wǒ bǐ dì di gāo。",
    "hsk2_bie": "Bié zài zhè lǐ shuō huà。",
    "hsk2_binguan": "Zhè jiā bīn guǎn lí jī chǎng hěn jìn。",
    "hsk2_chang": "Tā de tóu fa hěn cháng。",
    "hsk2_changge": "Wǒ men yì qǐ chàng gē ba。",
    "hsk2_chu": "Qǐng cóng zhè ge mén chū qù。",
    "hsk2_chuan": "Tā měi tiān chuān lán sè de yī fu。",
    "hsk2_ci": "Zhè shì wǒ dì yī cì lái zhōng guó。",
    "hsk2_cong": "Qǐng cóng zhè lǐ kāi shǐ dú。",
    "hsk2_cuo": "Zhè ge dá àn cuò le。",
    "hsk2_dalanqiu": "Xià wǔ wǒ men qù dǎ lán qiú。",
    "hsk2_dajia": "Dà jiā dōu zài jiào shì lǐ。",
    "hsk2_dao": "Qǐng nǐ bā diǎn dào gōng sī。",
    "hsk2_de2": "Nǐ pǎo de tài kuài le。",
    "hsk2_deng": "Wǒ zài mén kǒu děng nǐ。",
    "hsk2_didi": "Dì di jīn nián shí suì。",
    "hsk2_diyi": "Jīn tiān shì wǒ dì yī tiān shàng bān。",
    "hsk2_dong2": "Zhè běn shū wǒ kàn bù dǒng。",
    "hsk2_dui": "Zhè ge dì fang duì ma？",
    "hsk2_fangjian": "Qǐng jìn wǒ de fáng jiān。",
    "hsk2_feichang": "Wǒ fēi cháng xǐ huān zhè běn shū。",
    "hsk2_fuwuyuan": "Fú wù yuán zhèng zài ná cài dān。",
    "hsk2_gao": "Zhè ge zhuō zi tài gāo le。",
    "hsk2_gaosu": "Mā ma gào su wǒ yí ge shì qing。",
    "hsk2_gege": "Gē ge zài gōng sī shàng bān。",
    "hsk2_gei": "Qǐng gěi lǎo shī zhè běn shū。",
    "hsk2_gonggongqiche": "Gōng gòng qì chē mǎ shàng jiù lái。",
    "hsk2_gongsi": "Wǒ jiā lí gōng sī bù yuǎn。",
    "hsk2_gui": "Zhè ge píng guǒ bù guì。",
    "hsk2_guo": "Nǐ kàn guo zhè ge diàn yǐng ma？",
    "hsk2_hai": "Wǒ hái xiǎng hē yì bēi chá。",
    "hsk2_haizi": "Hái zi zài wài miàn wán。",
    "hsk2_haochi": "Zhè jiā diàn de miàn tiáo hěn hǎo chī。",
    "hsk2_hei": "Wǒ de shū bāo shì hēi de。",
    "hsk2_hong": "Tā xǐ huān hóng huā。",
    "hsk2_huochezhan": "Wǒ men zài huǒ chē zhàn jiàn。",
    "hsk2_jichang": "Jī chǎng lí zhè lǐ hěn yuǎn。",
    "hsk2_jidan": "Bīng xiāng lǐ yǒu jī dàn ma？",
    "hsk2_jian": "Zhè shì yí jiàn zhòng yào de shì qing。",
    "hsk2_jiaoshi": "Xué shēng dōu zài jiào shì xué xí。",
    "hsk2_jiejie": "Jiě jie xǐ huān hē kā fēi。",
    "hsk2_jieshao": "Qǐng jiè shào nǐ de péng you。",
    "hsk2_jin2": "Chāo shì jiù zài xué xiào fù jìn。",
    "hsk2_jin": "Bú yào jìn zhè ge fáng jiān。",
    "hsk2_jiu": "Tā yì huí jiā jiù shuì jiào。",
    "hsk2_juede": "Nǐ jué de zhè ge zěn me yàng？",
    "hsk2_kafei": "Zǎo shang wǒ bù hē kā fēi。",
    "hsk2_kaishi": "Diàn yǐng bā diǎn kāi shǐ。",
    "hsk2_kaoshi": "Míng tiān wǒ men kǎo shì。",
    "hsk2_keneng": "Míng tiān kě néng xià yǔ。",
    "hsk2_keyi": "Zhè lǐ kě yǐ zuò ma？",
    "hsk2_ke3": "Hàn yǔ kè jǐ diǎn kāi shǐ？",
    "hsk2_kuai2": "Qǐng kuài yì diǎn，wǒ men yào chí dào le。",
    "hsk2_kuaile": "Hái zi men wán de hěn kuài lè。",
    "hsk2_lei": "Pǎo bù yǐ hòu tā hěn lèi。",
    "hsk2_li": "Běi jīng lí Shàng hǎi hěn yuǎn。",
    "hsk2_liang": "Qǐng gěi wǒ liǎng bēi shuǐ。",
    "hsk2_ling": "Zhè ge hào mǎ zuì hòu shì líng。",
    "hsk2_lu": "Qǐng gào su wǒ qù xué xiào de lù。",
    "hsk2_luyou": "Qù nián wǒ men qù zhōng guó lǚ yóu。",
    "hsk2_mai": "Tā men mài kā fēi hé chá。",
    "hsk2_man": "Zhè liàng chē zǒu de hěn màn。",
    "hsk2_mang": "Mā ma xià wǔ bù máng。",
    "hsk2_mei": "Měi ge xué shēng dōu yǒu yì běn shū。",
    "hsk2_meimei": "Mèi mei zài xué xiào xué xí Hàn yǔ。",
    "hsk2_men": "Mén zài fáng jiān de yòu biān。",
    "hsk2_miantiao": "Zhè wǎn miàn tiáo hěn hǎo chī。",
    "hsk2_nan3": "Nà ge nán xué shēng shì wǒ gē ge。",
    "hsk2_nin": "Nín xiǎng hē chá ma？",
    "hsk2_niunai": "Qǐng gěi hái zi yì bēi niú nǎi。",
    "hsk2_nv": "Nà ge nǚ xué shēng shì wǒ jiě jie。",
    "hsk2_pangbian": "Qǐng zuò zài wǒ páng biān。",
    "hsk2_paobu": "Tā xǐ huān zài gōng yuán pǎo bù。",
    "hsk2_pianyi": "Zhè ge fáng jiān bù pián yi。",
    "hsk2_piao": "Nǐ de huǒ chē piào zài nǎ lǐ？",
    "hsk2_qizi": "Tā de qī zi zài jiā。",
    "hsk2_qichuang": "Hái zi měi tiān zǎo shang liù diǎn qǐ chuáng。",
    "hsk2_qian2": "Zhè běn shū yǒu yì qiān yè。",
    "hsk2_qianbi": "Qǐng yòng qiān bǐ xiě míng zi。",
    "hsk2_qing2": "Míng tiān huì shì qíng tiān ma？",
    "hsk2_qunian": "Qù nián dōng tiān hěn lěng。",
    "hsk2_rang": "Lǎo shī ràng wǒ men dú shū。",
    "hsk2_ri": "Wǒ de shēng rì shì shí yuè èr rì。",
    "hsk2_shangban": "Bà ba xīng qī yī bù shàng bān。",
    "hsk2_shenti": "Yùn dòng duì shēn tǐ hěn hǎo。",
    "hsk2_shengbing": "Tā shēng bìng le，bù néng shàng bān。",
    "hsk2_shengri": "Zhù nǐ shēng rì kuài lè！",
    "hsk2_shijian": "Xiàn zài méi yǒu shí jiān chī fàn。",
    "hsk2_shiqing": "Zhè jiàn shì qing hěn zhòng yào。",
    "hsk2_shoubiao": "Nǐ de shǒu biǎo hěn piào liang。",
    "hsk2_shouji": "Qǐng yòng shǒu jī gěi wǒ dǎ diàn huà。",
    "hsk2_shuohua": "Tā zhèng zài gēn lǎo shī shuō huà。",
    "hsk2_song": "Wǒ sòng péng you qù jī chǎng。",
    "hsk2_suiran_danshi": "Suī rán hěn lèi，dàn shì tā hái zài xué xí。",
    "hsk2_ta3": "Wǒ de shǒu jī zài zhè lǐ，tā hěn xīn。",
    "hsk2_tizuqiu": "Gē ge xià wǔ qù tī zú qiú。",
    "hsk2_ti": "Lǎo shī zài wèn yí ge tí。",
    "hsk2_tiaowu": "Wǎn shang wǒ men yì qǐ tiào wǔ ba。",
    "hsk2_wai": "Wài miàn hěn lěng，qǐng jìn lái。",
    "hsk2_wan2": "Qǐng xiě wán zhè ge tí。",
    "hsk2_wan": "Wǒ men qù gōng yuán wán ba。",
    "hsk2_wanshang": "Wǒ wǎn shang kàn shū。",
    "hsk2_wang": "Huǒ chē wǎng Běi jīng kāi。",
    "hsk2_weishenme": "Tā wèi shén me bù lái？",
    "hsk2_wen": "Qǐng wèn lǎo shī zhè ge tí。",
    "hsk2_wenti": "Nǐ yǒu shén me wèn tí ma？",
    "hsk2_xigua": "Zhè ge xī guā hěn tián。",
    "hsk2_xiwang": "Xī wàng míng tiān tiān qì hǎo。",
    "hsk2_xi": "Qǐng xǐ nǐ de shǒu。",
    "hsk2_xiaoshi": "Cóng zhè lǐ dào jī chǎng yào yí ge xiǎo shí。",
    "hsk2_xiao": "Tīng dào zhè ge gù shi，dà jiā dōu xiào le。",
    "hsk2_xin": "Zhè shì wǒ de xīn shǒu jī。",
    "hsk2_xing": "Wǒ xìng Wáng，tā xìng Lǐ。",
    "hsk2_xiuxi": "Wǒ men zhōng wǔ xiū xi yí ge xiǎo shí。",
    "hsk2_xue": "Hái zi xǐ huān zài xuě lǐ wán。",
    "hsk2_yanse": "Zhè jiàn yī fu de yán sè hěn hǎo kàn。",
    "hsk2_yanjing": "Bú yào yòng shǒu pèng yǎn jing。",
    "hsk2_yangrou": "Zhè jiā diàn de yáng ròu hěn hǎo chī。",
    "hsk2_yao": "Nǐ yào qù xué xiào ma？",
    "hsk2_yao2": "Zhè ge yào yì tiān chī liǎng cì。",
    "hsk2_ye": "Tā yě huì shuō Hàn yǔ。",
    "hsk2_yixia": "Wǒ xiǎng wèn nǐ yí xià。",
    "hsk2_yijing": "Wǒ yǐ jīng chī guo fàn le。",
    "hsk2_yiqi": "Wǒ hé jiě jie yì qǐ xué xí。",
    "hsk2_yisi": "Wǒ bù dǒng zhè ge cí de yì si。",
    "hsk2_yin": "Yīn tiān de shí hou bù rè。",
    "hsk2_yinwei_suoyi": "Yīn wèi hěn máng，suǒ yǐ tā méi lái。",
    "hsk2_youyong": "Xià tiān wǒ men qù yóu yǒng。",
    "hsk2_youbian": "Qǐng zuò zài wǒ de yòu biān。",
    "hsk2_yu": "Jīn tiān de yú hěn xīn xiān。",
    "hsk2_yuan": "Wǒ jiā lí zhè lǐ bù yuǎn。",
    "hsk2_yundong": "Měi tiān yùn dòng duì shēn tǐ hǎo。",
    "hsk2_zai2": "Míng tiān wǒ men zài jiàn。",
    "hsk2_zaoshang": "Zǎo shang hǎo，nǐ chī fàn le ma？",
    "hsk2_zhangfu": "Tā de zhàng fu zài gōng sī gōng zuò。",
    "hsk2_zhao": "Nǐ zài zhǎo shén me？",
    "hsk2_zhe2": "Mén kāi zhe，qǐng jìn。",
    "hsk2_zhen": "Jīn tiān tiān qì zhēn hǎo。",
    "hsk2_zhengzai": "Mā ma zhèng zài zuò fàn。",
    "hsk2_zhi": "Zhè lǐ zhǐ yǒu yí ge rén。",
    "hsk2_zhidao": "Wǒ bù zhī dào zhè ge dì fang。",
    "hsk2_zhunbei": "Qǐng zhǔn bèi hǎo nǐ de shū。",
    "hsk2_zou": "Tā měi tiān zǒu lù qù gōng sī。",
    "hsk2_zui": "Wǒ zuì xǐ huān zhè ge yán sè。",
    "hsk2_zuobian": "Qǐng zuò zài wǒ de zuǒ biān。",
}

HSK2_VOCAB = [
    entry[:5] + (AUDIO_SENTENCE_PINYIN[entry[0]],) + entry[5:7]
    + (READING_SENTENCE_PINYIN[entry[0]],) + entry[7:]
    for entry in HSK2_VOCAB
]


CSS = """
.card {
  font-family: Arial, "Noto Sans CJK SC", sans-serif;
  font-size: 20px;
  text-align: center;
  padding: 20px;
}
.word { font-size: 48px; margin: 18px 0 8px; }
.pinyin { color: #555; font-size: 22px; margin: 6px 0; }
.german { font-size: 20px; margin: 8px 0; }
.sentence { font-size: 30px; margin: 12px 0; }
.hint { color: #666; font-size: 15px; }
.audio-control { margin: 28px 0; }
.audio-control .replay-button { font-size: 32px; }
hr { border: 0; border-top: 1px solid #ddd; margin: 18px 0; }
.nightMode .card { color: #ddd; }
.nightMode .pinyin, .nightMode .hint { color: #bbb; }
.nightMode hr { border-top-color: #555; }
"""

FIELDS = [
    {"name": "Hanzi"},
    {"name": "Pinyin"},
    {"name": "Meaning"},
    {"name": "AudioSentenceCN"},
    {"name": "AudioSentenceSound"},
    {"name": "AudioSentencePY"},
    {"name": "AudioSentenceDE"},
    {"name": "ReadingSentenceCN"},
    {"name": "ReadingSentencePY"},
    {"name": "ReadingSentenceDE"},
]

TEMPLATES = [
    {
        "name": "1. Leseverstehen",
        "qfmt": """\
<div class="sentence">{{ReadingSentenceCN}}</div>
""",
        "afmt": """\
{{FrontSide}}
<hr>
<div class="pinyin">{{ReadingSentencePY}}</div>
<div class="german">{{ReadingSentenceDE}}</div>
<div class="word">{{Hanzi}}</div>
<div class="pinyin">[{{Pinyin}}]</div>
<div class="german">{{Meaning}}</div>
""",
    },
    {
        "name": "2. Hörverstehen",
        "qfmt": """\
<div class="audio-control">{{AudioSentenceSound}}</div>
<div class="hint">Audio wiederholen</div>
""",
        "afmt": """\
{{FrontSide}}
<hr>
<div class="sentence">{{AudioSentenceCN}}</div>
<div class="pinyin">{{AudioSentencePY}}</div>
<div class="german">{{AudioSentenceDE}}</div>
<div class="word">{{Hanzi}}</div>
<div class="pinyin">[{{Pinyin}}]</div>
<div class="german">{{Meaning}}</div>
""",
    },
    {
        "name": "3. Wortschatz",
        "qfmt": """\
<div class="word">{{Hanzi}}</div>
""",
        "afmt": """\
{{FrontSide}}
<hr>
<div class="pinyin">{{Pinyin}}</div>
<div class="german">{{Meaning}}</div>
""",
    },
]


def validate_deck_structure() -> None:
    """Keep the three task templates and their field contracts in sync."""
    expected_fields = [
        "Hanzi",
        "Pinyin",
        "Meaning",
        "AudioSentenceCN",
        "AudioSentenceSound",
        "AudioSentencePY",
        "AudioSentenceDE",
        "ReadingSentenceCN",
        "ReadingSentencePY",
        "ReadingSentenceDE",
    ]
    if [field["name"] for field in FIELDS] != expected_fields:
        raise ValueError("The model must have exactly the ten expected fields.")

    if [template["name"] for template in TEMPLATES] != [
            "1. Leseverstehen", "2. Hörverstehen", "3. Wortschatz"]:
        raise ValueError("The model must contain reading, listening, and vocabulary templates.")

    reading, listening, vocabulary = TEMPLATES
    reading_front_fields = re.findall(r"{{([^}]+)}}", reading["qfmt"])
    if reading_front_fields != ["ReadingSentenceCN"] or reading["qfmt"].strip() != (
            '<div class="sentence">{{ReadingSentenceCN}}</div>'):
        raise ValueError("The reading-card front must show only its reading sentence.")
    if "{{ReadingSentencePY}}" not in reading["afmt"] or "{{Hanzi}}" not in reading["afmt"]:
        raise ValueError("The reading-card back must reveal its pinyin and focus word.")
    listening_front_fields = re.findall(r"{{([^}]+)}}", listening["qfmt"])
    if listening_front_fields != ["AudioSentenceSound"]:
        raise ValueError("The listening-card front must show only the embedded sound control.")
    if "{{AudioSentenceCN}}" not in listening["afmt"] or "{{Hanzi}}" not in listening["afmt"]:
        raise ValueError("The listening-card back must reveal the sentence and focus word.")
    vocabulary_front_fields = re.findall(r"{{([^}]+)}}", vocabulary["qfmt"])
    if vocabulary_front_fields != ["Hanzi"]:
        raise ValueError("The vocabulary-card front must show only the isolated word.")
    if "{{Pinyin}}" not in vocabulary["afmt"] or "{{Meaning}}" not in vocabulary["afmt"]:
        raise ValueError("The vocabulary-card back must reveal pinyin and meaning.")


def validate_vocabulary() -> None:
    """Fail early if this self-contained source no longer describes HSK 2.0."""
    if len(OFFICIAL_HSK2_WORDS) != 150 or len(HSK2_VOCAB) != 150:
        raise ValueError("HSK 2.0 must contain exactly 150 vocabulary entries.")

    words = [entry[1] for entry in HSK2_VOCAB]
    ids = [entry[0] for entry in HSK2_VOCAB]
    if tuple(words) != OFFICIAL_HSK2_WORDS:
        raise ValueError("HSK2_VOCAB does not match the official HSK 2.0 order.")
    if len(set(words)) != 150 or len(set(ids)) != 150:
        raise ValueError("Vocabulary words and stable IDs must be unique.")
    if set(AUDIO_SENTENCE_PINYIN) != set(ids):
        raise ValueError("Every HSK 2 entry must have one hard-coded audio-sentence pinyin value.")
    if set(READING_SENTENCE_PINYIN) != set(ids):
        raise ValueError("Every HSK 2 entry must have one hard-coded reading-sentence pinyin value.")

    for entry in HSK2_VOCAB:
        if len(entry) != 11 or not entry[0].startswith("hsk2_"):
            raise ValueError(f"Invalid vocabulary entry: {entry!r}")
        (_, word, pinyin, german, audio_zh, audio_py, audio_de, reading_zh,
         reading_py, reading_de, filename) = entry
        if not all((word, pinyin, german, audio_zh, audio_py, audio_de, reading_zh,
                    reading_py, reading_de, filename)):
            raise ValueError(f"Blank field in vocabulary entry {entry[0]!r}.")
        if audio_zh == reading_zh:
            raise ValueError(f"Examples must differ for {entry[0]!r}.")
        if filename != f"{entry[0]}.mp3":
            raise ValueError(f"Unexpected audio filename for {entry[0]!r}.")
        if not PINYIN_VALUE_PATTERN.fullmatch(reading_py) or re.search(
                r"\b(?:todo|tbd|placeholder|pinyin)\b", reading_py, re.IGNORECASE):
            raise ValueError(f"Invalid reading-sentence pinyin for {entry[0]!r}.")


def validate_generated_package(output_path: Path, expected_audio: set[str]) -> None:
    """Verify the written Anki package, not just the in-memory deck."""
    with zipfile.ZipFile(output_path) as package:
        collection_name = "collection.anki2"
        if collection_name not in package.namelist():
            raise ValueError("Generated package does not contain an Anki collection.")

        connection = sqlite3.connect(":memory:")
        try:
            connection.deserialize(package.read(collection_name))
            note_count = connection.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
            card_count = connection.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
        finally:
            connection.close()

        media = json.loads(package.read("media"))
        embedded_audio = set(media.values())

    if note_count != 150 or card_count != 450:
        raise ValueError(
            f"Generated package has {note_count} notes and {card_count} cards; expected 150 and 450."
        )
    if embedded_audio != expected_audio:
        raise ValueError(
            f"Generated package embeds {len(embedded_audio)} expected sentence-audio files; "
            "expected all 150."
        )


def build_deck(output_path: Path) -> None:
    """Create and verify the package with every listening-sentence MP3 embedded."""
    validate_deck_structure()
    validate_vocabulary()
    model = genanki.Model(MODEL_ID, DECK_NAME, fields=FIELDS, templates=TEMPLATES, css=CSS)
    deck = genanki.Deck(DECK_ID, DECK_NAME)
    media_files = []

    for (vocab_id, chinese, pinyin, german, audio_zh, audio_py, audio_de, reading_zh,
         reading_py, reading_de, filename) in HSK2_VOCAB:
        audio_path = AUDIO_DIR / filename
        if not audio_path.is_file():
            raise FileNotFoundError(f"Required listening audio is missing: {audio_path}")
        media_files.append(str(audio_path))

        deck.add_note(genanki.Note(
            model=model,
            guid=genanki.guid_for("hsk2-german-standalone", vocab_id),
            fields=[
                chinese, pinyin, german, audio_zh, f"[sound:{filename}]", audio_py, audio_de,
                reading_zh, reading_py, reading_de,
            ],
        ))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file(str(output_path))
    validate_generated_package(output_path, {path.name for path in map(Path, media_files)})

    print(f"Created {output_path}")
    print("  150 vocabulary entries -> 450 cards (3 templates per entry)")
    print(f"  Sentence audio files embedded: {len(media_files)}/150")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=SCRIPT_DIR / OUTPUT_FILE,
        help=f"output .apkg path (default: {OUTPUT_FILE} next to this script)",
    )
    args = parser.parse_args()
    build_deck(args.output.expanduser().resolve())


if __name__ == "__main__":
    main()
