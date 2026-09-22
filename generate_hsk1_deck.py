#!/usr/bin/env python3
"""Build a German-language Anki deck for the 150-word HSK 1.0 vocabulary.

Usage:
    python3 generate_hsk1_deck.py
    python3 generate_hsk1_deck.py --output /path/to/HSK1_DualTask_Deck.apkg

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


MODEL_ID = 1607392386
DECK_ID = 2059384719
DECK_NAME = "HSK 1 - Offizieller Wortschatz (Hör- & Leseverstehen)"
OUTPUT_FILE = "HSK1_DualTask_Deck.apkg"
SCRIPT_DIR = Path(__file__).resolve().parent
AUDIO_DIR = SCRIPT_DIR / "audio"
PINYIN_VALUE_PATTERN = re.compile(r"^[A-Za-zÀ-ɏ ，。！？、：]+$")

# The order is the official HSK 1.0 list of 150 vocabulary words. Every
# vocabulary row is expanded with hard-coded pinyin transcriptions below.
OFFICIAL_HSK1_WORDS = (
    '爱', '八', '爸爸', '杯子', '北京', '本', '不客气', '不', '菜', '茶',
    '吃', '出租车', '打电话', '大', '的', '点', '电脑', '电视', '电影', '东西',
    '都', '读', '对不起', '多', '多少', '儿子', '二', '饭店', '飞机', '分钟',
    '高兴', '个', '工作', '狗', '汉语', '好', '号', '喝', '和', '很',
    '后面', '回', '会', '几', '家', '叫', '今天', '九', '开', '看',
    '看见', '块', '来', '老师', '了', '冷', '里', '六', '妈妈', '吗',
    '买', '猫', '没关系', '没有', '米饭', '明天', '名字', '哪', '哪儿', '那',
    '呢', '能', '你', '年', '女儿', '朋友', '漂亮', '苹果', '七', '钱',
    '前面', '请', '去', '热', '人', '认识', '三', '商店', '上', '上午',
    '少', '谁', '什么', '十', '时候', '是', '书', '水', '水果', '睡觉',
    '说', '四', '岁', '他', '她', '太', '天气', '听', '同学', '喂',
    '我', '我们', '五', '喜欢', '下', '下午', '下雨', '先生', '现在', '想',
    '小', '小姐', '些', '写', '谢谢', '星期', '学生', '学习', '学校', '一',
    '一点儿', '衣服', '医生', '医院', '椅子', '有', '月', '在', '再见', '怎么',
    '怎么样', '这', '中国', '中午', '住', '桌子', '字', '昨天', '坐', '做',
)

OFFICIAL_HSK1_POS = {
    '爱': '动',
    '八': '数',
    '爸爸': '名',
    '杯子': '名',
    '北京': '名',
    '本': '量',
    '不客气': '叹',
    '不': '副',
    '菜': '名',
    '茶': '名',
    '吃': '动',
    '出租车': '名',
    '打电话': '动',
    '大': '形',
    '的': '助',
    '点': '量/名',
    '电脑': '名',
    '电视': '名',
    '电影': '名',
    '东西': '名',
    '都': '副',
    '读': '动',
    '对不起': '动',
    '多': '形',
    '多少': '代',
    '儿子': '名',
    '二': '数',
    '饭店': '名',
    '飞机': '名',
    '分钟': '量',
    '高兴': '形',
    '个': '量',
    '工作': '动/名',
    '狗': '名',
    '汉语': '名',
    '好': '形',
    '号': '名/量',
    '喝': '动',
    '和': '连/介',
    '很': '副',
    '后面': '名',
    '回': '动',
    '会': '动',
    '几': '数/代',
    '家': '名/量',
    '叫': '动',
    '今天': '名',
    '九': '数',
    '开': '动',
    '看': '动',
    '看见': '动',
    '块': '量',
    '来': '动',
    '老师': '名',
    '了': '助',
    '冷': '形',
    '里': '名',
    '六': '数',
    '妈妈': '名',
    '吗': '助',
    '买': '动',
    '猫': '名',
    '没关系': '叹',
    '没有': '动/副',
    '米饭': '名',
    '明天': '名',
    '名字': '名',
    '哪': '代',
    '哪儿': '代',
    '那': '代',
    '呢': '助',
    '能': '动',
    '你': '代',
    '年': '名/量',
    '女儿': '名',
    '朋友': '名',
    '漂亮': '形',
    '苹果': '名',
    '七': '数',
    '钱': '名',
    '前面': '名',
    '请': '动',
    '去': '动',
    '热': '形',
    '人': '名',
    '认识': '动',
    '三': '数',
    '商店': '名',
    '上': '名/动',
    '上午': '名',
    '少': '形',
    '谁': '代',
    '什么': '代',
    '十': '数',
    '时候': '名',
    '是': '动',
    '书': '名',
    '水': '名',
    '水果': '名',
    '睡觉': '动',
    '说': '动',
    '四': '数',
    '岁': '量',
    '他': '代',
    '她': '代',
    '太': '副',
    '天气': '名',
    '听': '动',
    '同学': '名',
    '喂': '叹',
    '我': '代',
    '我们': '代',
    '五': '数',
    '喜欢': '动',
    '下': '名/动/量',
    '下午': '名',
    '下雨': '动',
    '先生': '名',
    '现在': '名',
    '想': '动',
    '小': '形',
    '小姐': '名',
    '些': '量',
    '写': '动',
    '谢谢': '动',
    '星期': '名',
    '学生': '名',
    '学习': '动',
    '学校': '名',
    '一': '数',
    '一点儿': '数量',
    '衣服': '名',
    '医生': '名',
    '医院': '名',
    '椅子': '名',
    '有': '动',
    '月': '名',
    '在': '动/介/副',
    '再见': '动',
    '怎么': '代',
    '怎么样': '代',
    '这': '代',
    '中国': '名',
    '中午': '名',
    '住': '动',
    '桌子': '名',
    '字': '名',
    '昨天': '名',
    '坐': '动',
    '做': '动',
}

HSK1_VOCAB = [
    ('hsk1_ai', '爱', 'ài', 'lieben', '我爱我的家人。', 'Ich liebe meine Familie.', '请读：我爱我的家人。', 'Lies: Ich liebe meine Familie.', 'hsk1_ai.mp3'),
    ('hsk1_ba2', '八', 'bā', 'acht', '我有八本书。', 'Ich habe acht Bücher.', '请读：我有八本书。', 'Lies: Ich habe acht Bücher.', 'hsk1_ba2.mp3'),
    ('hsk1_ba', '爸爸', 'bàba', 'Papa / Vater', '我爸爸在家工作。', 'Mein Papa arbeitet zu Hause.', '请读：我爸爸在家工作。', 'Lies: Mein Papa arbeitet zu Hause.', 'hsk1_ba.mp3'),
    ('hsk1_beizi', '杯子', 'bēizi', 'Tasse / Becher', '请给我一个杯子。', 'Bitte gib mir eine Tasse.', '请读：请给我一个杯子。', 'Lies: Bitte gib mir eine Tasse.', 'hsk1_beizi.mp3'),
    ('hsk1_beijing', '北京', 'Běijīng', 'Peking', '北京是中国的首都。', 'Peking ist die Hauptstadt Chinas.', '请读：北京是中国的首都。', 'Lies: Peking ist die Hauptstadt Chinas.', 'hsk1_beijing.mp3'),
    ('hsk1_ben', '本', 'běn', 'Zählwort für Bücher', '我买了三本书。', 'Ich habe drei Bücher gekauft.', '请读：我买了三本书。', 'Lies: Ich habe drei Bücher gekauft.', 'hsk1_ben.mp3'),
    ('hsk1_bukeqi', '不客气', 'bù kèqi', 'gern geschehen', '谢谢你！不客气。', 'Danke! Gern geschehen.', '请读：谢谢你！不客气。', 'Lies: Danke! Gern geschehen.', 'hsk1_bukeqi.mp3'),
    ('hsk1_bu', '不', 'bù', 'nicht / nein', '我不喝咖啡，我喝茶。', 'Ich trinke keinen Kaffee, ich trinke Tee.', '请读：我不喝咖啡，我喝茶。', 'Lies: Ich trinke keinen Kaffee, ich trinke Tee.', 'hsk1_bu.mp3'),
    ('hsk1_cai', '菜', 'cài', 'Gericht / Gemüse', '这道菜很好吃。', 'Dieses Gericht ist sehr lecker.', '请读：这道菜很好吃。', 'Lies: Dieses Gericht ist sehr lecker.', 'hsk1_cai.mp3'),
    ('hsk1_cha', '茶', 'chá', 'Tee', '我每天喝茶。', 'Ich trinke jeden Tag Tee.', '请读：我每天喝茶。', 'Lies: Ich trinke jeden Tag Tee.', 'hsk1_cha.mp3'),
    ('hsk1_chi', '吃', 'chī', 'essen', '我喜欢吃米饭。', 'Ich esse gern Reis.', '请读：我喜欢吃米饭。', 'Lies: Ich esse gern Reis.', 'hsk1_chi.mp3'),
    ('hsk1_chuzuche', '出租车', 'chūzūchē', 'Taxi', '我坐出租车去机场。', 'Ich fahre mit dem Taxi zum Flughafen.', '请读：我坐出租车去机场。', 'Lies: Ich fahre mit dem Taxi zum Flughafen.', 'hsk1_chuzuche.mp3'),
    ('hsk1_dadianhua', '打电话', 'dǎ diànhuà', 'telefonieren / anrufen', '我给妈妈打电话。', 'Ich rufe meine Mama an.', '请读：我给妈妈打电话。', 'Lies: Ich rufe meine Mama an.', 'hsk1_dadianhua.mp3'),
    ('hsk1_da', '大', 'dà', 'groß', '这个苹果很大。', 'Dieser Apfel ist sehr groß.', '请读：这个苹果很大。', 'Lies: Dieser Apfel ist sehr groß.', 'hsk1_da.mp3'),
    ('hsk1_de', '的', 'de', 'Possessiv-/Attributpartikel', '这是我的书。', 'Das ist mein Buch.', '请读：这是我的书。', 'Lies: Das ist mein Buch.', 'hsk1_de.mp3'),
    ('hsk1_dian', '点', 'diǎn', 'Uhr / Punkt / ein wenig', '现在是三点。', 'Es ist jetzt drei Uhr.', '请读：现在是三点。', 'Lies: Es ist jetzt drei Uhr.', 'hsk1_dian.mp3'),
    ('hsk1_diannao', '电脑', 'diànnǎo', 'Computer', '他用电脑工作。', 'Er arbeitet mit dem Computer.', '请读：他用电脑工作。', 'Lies: Er arbeitet mit dem Computer.', 'hsk1_diannao.mp3'),
    ('hsk1_dianshi', '电视', 'diànshì', 'Fernseher / Fernsehen', '我每天晚上看电视。', 'Ich sehe jeden Abend fern.', '请读：我每天晚上看电视。', 'Lies: Ich sehe jeden Abend fern.', 'hsk1_dianshi.mp3'),
    ('hsk1_dianying', '电影', 'diànyǐng', 'Film / Kino', '我周末喜欢看电影。', 'Ich sehe am Wochenende gern Filme.', '请读：我周末喜欢看电影。', 'Lies: Ich sehe am Wochenende gern Filme.', 'hsk1_dianying.mp3'),
    ('hsk1_dongxi', '东西', 'dōngxi', 'Sache / Dinge', '你买了什么东西？', 'Was hast du gekauft?', '请读：你买了什么东西？', 'Lies: Was hast du gekauft?', 'hsk1_dongxi.mp3'),
    ('hsk1_dou', '都', 'dōu', 'alle / beide', '我们都是学生。', 'Wir sind alle Schüler.', '请读：我们都是学生。', 'Lies: Wir sind alle Schüler.', 'hsk1_dou.mp3'),
    ('hsk1_du', '读', 'dú', 'lesen', '我读书。', 'Ich lese.', '请读：我读书。', 'Lies: Ich lese.', 'hsk1_du.mp3'),
    ('hsk1_duibuqi', '对不起', 'duìbuqǐ', 'Entschuldigung / es tut mir leid', '对不起，我来晚了。', 'Entschuldigung, ich bin zu spät gekommen.', '请读：对不起，我来晚了。', 'Lies: Entschuldigung, ich bin zu spät gekommen.', 'hsk1_duibuqi.mp3'),
    ('hsk1_duo', '多', 'duō', 'viel / viele', '这里有很多人。', 'Hier sind viele Leute.', '请读：这里有很多人。', 'Lies: Hier sind viele Leute.', 'hsk1_duo.mp3'),
    ('hsk1_duoshao', '多少', 'duōshao', 'wie viel / wie viele', '这个多少钱？', 'Wie viel kostet das?', '请读：这个多少钱？', 'Lies: Wie viel kostet das?', 'hsk1_duoshao.mp3'),
    ('hsk1_erzi', '儿子', 'érzi', 'Sohn', '他有一个聪明的儿子。', 'Er hat einen klugen Sohn.', '请读：他有一个聪明的儿子。', 'Lies: Er hat einen klugen Sohn.', 'hsk1_erzi.mp3'),
    ('hsk1_er', '二', 'èr', 'zwei', '我有两个哥哥。', 'Ich habe zwei ältere Brüder.', '请读：我有两个哥哥。', 'Lies: Ich habe zwei ältere Brüder.', 'hsk1_er.mp3'),
    ('hsk1_fandian', '饭店', 'fàndiàn', 'Restaurant', '这家饭店很好。', 'Dieses Restaurant ist sehr gut.', '请读：这家饭店很好。', 'Lies: Dieses Restaurant ist sehr gut.', 'hsk1_fandian.mp3'),
    ('hsk1_feiji', '飞机', 'fēijī', 'Flugzeug', '我坐飞机去上海。', 'Ich fliege nach Shanghai.', '请读：我坐飞机去上海。', 'Lies: Ich fliege nach Shanghai.', 'hsk1_feiji.mp3'),
    ('hsk1_fenzhong', '分钟', 'fēnzhōng', 'Minute', '请等我五分钟。', 'Bitte warte fünf Minuten auf mich.', '请读：请等我五分钟。', 'Lies: Bitte warte fünf Minuten auf mich.', 'hsk1_fenzhong.mp3'),
    ('hsk1_gaoxing', '高兴', 'gāoxìng', 'froh / glücklich', '见到你我很高兴。', 'Ich freue mich sehr, dich zu sehen.', '请读：见到你我很高兴。', 'Lies: Ich freue mich sehr, dich zu sehen.', 'hsk1_gaoxing.mp3'),
    ('hsk1_ge', '个', 'gè', 'allgemeines Zählwort', '请给我一个苹果。', 'Bitte gib mir einen Apfel.', '请读：请给我一个苹果。', 'Lies: Bitte gib mir einen Apfel.', 'hsk1_ge.mp3'),
    ('hsk1_gongzuo', '工作', 'gōngzuò', 'arbeiten / Arbeit', '他在银行工作。', 'Er arbeitet in einer Bank.', '请读：他在银行工作。', 'Lies: Er arbeitet in einer Bank.', 'hsk1_gongzuo.mp3'),
    ('hsk1_gou', '狗', 'gǒu', 'Hund', '我家有一只狗。', 'Wir haben zu Hause einen Hund.', '请读：我家有一只狗。', 'Lies: Wir haben zu Hause einen Hund.', 'hsk1_gou.mp3'),
    ('hsk1_hanyu', '汉语', 'Hànyǔ', 'Chinesisch', '我在学习汉语。', 'Ich lerne Chinesisch.', '请读：我在学习汉语。', 'Lies: Ich lerne Chinesisch.', 'hsk1_hanyu.mp3'),
    ('hsk1_hao', '好', 'hǎo', 'gut', '今天天气很好。', 'Das Wetter ist heute sehr schön.', '请读：今天天气很好。', 'Lies: Das Wetter ist heute sehr schön.', 'hsk1_hao.mp3'),
    ('hsk1_hao2', '号', 'hào', 'Datum / Nummer', '今天几号？', 'Den Wievielten haben wir heute?', '请读：今天几号？', 'Lies: Den Wievielten haben wir heute?', 'hsk1_hao2.mp3'),
    ('hsk1_he', '喝', 'hē', 'trinken', '我想喝一杯茶。', 'Ich möchte eine Tasse Tee trinken.', '请读：我想喝一杯茶。', 'Lies: Ich möchte eine Tasse Tee trinken.', 'hsk1_he.mp3'),
    ('hsk1_he2', '和', 'hé', 'und / mit', '我和你是朋友。', 'Du und ich sind Freunde.', '请读：我和你是朋友。', 'Lies: Du und ich sind Freunde.', 'hsk1_he2.mp3'),
    ('hsk1_hen', '很', 'hěn', 'sehr', '我今天很高兴。', 'Ich bin heute sehr froh.', '请读：我今天很高兴。', 'Lies: Ich bin heute sehr froh.', 'hsk1_hen.mp3'),
    ('hsk1_houmian', '后面', 'hòumiàn', 'hinten / hinter', '他在我后面。', 'Er ist hinter mir.', '请读：他在我后面。', 'Lies: Er ist hinter mir.', 'hsk1_houmian.mp3'),
    ('hsk1_hui2', '回', 'huí', 'zurückkehren', '我下午回家。', 'Ich gehe am Nachmittag wieder nach Hause.', '请读：我下午回家。', 'Lies: Ich gehe am Nachmittag nach Hause zurück.', 'hsk1_hui2.mp3'),
    ('hsk1_hui', '会', 'huì', 'können / wissen, wie man', '我会说一点汉语。', 'Ich kann ein bisschen Chinesisch sprechen.', '请读：我会说一点汉语。', 'Lies: Ich kann ein bisschen Chinesisch sprechen.', 'hsk1_hui.mp3'),
    ('hsk1_ji', '几', 'jǐ', 'wie viele / einige', '你有几个朋友？', 'Wie viele Freunde hast du?', '请读：你有几个朋友？', 'Lies: Wie viele Freunde hast du?', 'hsk1_ji.mp3'),
    ('hsk1_jia', '家', 'jiā', 'Zuhause / Familie', '我家在北京附近。', 'Mein Zuhause ist in der Nähe von Peking.', '请读：我家在北京附近。', 'Lies: Mein Zuhause ist in der Nähe von Peking.', 'hsk1_jia.mp3'),
    ('hsk1_jiao', '叫', 'jiào', 'heißen / nennen', '我叫小明。', 'Ich heiße Xiao Ming.', '请读：我叫小明。', 'Lies: Ich heiße Xiao Ming.', 'hsk1_jiao.mp3'),
    ('hsk1_jintian', '今天', 'jīntiān', 'heute', '今天是星期几？', 'Welcher Wochentag ist heute?', '请读：今天是星期几？', 'Lies: Welcher Wochentag ist heute?', 'hsk1_jintian.mp3'),
    ('hsk1_jiu', '九', 'jiǔ', 'neun', '一个月有三十天，我工作了九天。', 'Ein Monat hat dreißig Tage, ich habe neun Tage gearbeitet.', '请读：一个月有三十天，我工作了九天。', 'Lies: Ein Monat hat dreißig Tage, ich habe neun Tage gearbeitet.', 'hsk1_jiu.mp3'),
    ('hsk1_kai', '开', 'kāi', 'öffnen / anfangen', '请开门。', 'Bitte mach die Tür auf.', '请读：请开门。', 'Lies: Bitte mach die Tür auf.', 'hsk1_kai.mp3'),
    ('hsk1_kan', '看', 'kàn', 'schauen / ansehen / lesen', '我们一起看书吧。', 'Lass uns zusammen lesen.', '请读：我们一起看书吧。', 'Lies: Lass uns zusammen lesen.', 'hsk1_kan.mp3'),
    ('hsk1_kanjian', '看见', 'kànjiàn', 'sehen', '我看见他了。', 'Ich habe ihn gesehen.', '请读：我看见他了。', 'Lies: Ich habe ihn gesehen.', 'hsk1_kanjian.mp3'),
    ('hsk1_kuai', '块', 'kuài', 'Yuan / Stück', '这个苹果一块钱。', 'Dieser Apfel kostet einen Yuan.', '请读：这个苹果一块钱。', 'Lies: Dieser Apfel kostet einen Yuan.', 'hsk1_kuai.mp3'),
    ('hsk1_lai', '来', 'lái', 'kommen', '请你来我家吃饭。', 'Bitte komm zu mir nach Hause zum Essen.', '请读：请你来我家吃饭。', 'Lies: Bitte komm zu mir nach Hause zum Essen.', 'hsk1_lai.mp3'),
    ('hsk1_laoshi', '老师', 'lǎoshī', 'Lehrer / Lehrerin', '我的老师很好。', 'Mein Lehrer ist sehr gut.', '请读：我的老师很好。', 'Lies: Mein Lehrer ist sehr gut.', 'hsk1_laoshi.mp3'),
    ('hsk1_le', '了', 'le', 'Perfektpartikel', '我吃了早饭。', 'Ich habe gefrühstückt.', '请读：我吃了早饭。', 'Lies: Ich habe gefrühstückt.', 'hsk1_le.mp3'),
    ('hsk1_leng', '冷', 'lěng', 'kalt', '今天很冷。', 'Heute ist es sehr kalt.', '请读：今天很冷。', 'Lies: Heute ist es sehr kalt.', 'hsk1_leng.mp3'),
    ('hsk1_li', '里', 'lǐ', 'in / innen', '书包里有很多书。', 'Im Schulranzen sind viele Bücher.', '请读：书包里有很多书。', 'Lies: Im Schulranzen sind viele Bücher.', 'hsk1_li.mp3'),
    ('hsk1_liu', '六', 'liù', 'sechs', '一个星期有七天，我上了六天课。', 'Eine Woche hat sieben Tage, ich hatte an sechs Tagen Unterricht.', '请读：一个星期有七天，我上了六天课。', 'Lies: Eine Woche hat sieben Tage, ich hatte an sechs Tagen Unterricht.', 'hsk1_liu.mp3'),
    ('hsk1_mama', '妈妈', 'māma', 'Mama / Mutter', '我妈妈在家做饭。', 'Meine Mama kocht zu Hause.', '请读：我妈妈在家做饭。', 'Lies: Meine Mama kocht zu Hause.', 'hsk1_mama.mp3'),
    ('hsk1_ma', '吗', 'ma', 'Fragepartikel', '你喜欢吃饺子吗？', 'Isst du gern Jiaozi?', '请读：你喜欢吃饺子吗？', 'Lies: Isst du gern Jiaozi?', 'hsk1_ma.mp3'),
    ('hsk1_mai', '买', 'mǎi', 'kaufen', '我买了一本书。', 'Ich habe ein Buch gekauft.', '请读：我买了一本书。', 'Lies: Ich habe ein Buch gekauft.', 'hsk1_mai.mp3'),
    ('hsk1_mao', '猫', 'māo', 'Katze', '我有一只猫。', 'Ich habe eine Katze.', '请读：我有一只猫。', 'Lies: Ich habe eine Katze.', 'hsk1_mao.mp3'),
    ('hsk1_meiguanxi', '没关系', 'méi guānxi', 'macht nichts / kein Problem', '没关系，不要担心。', 'Kein Problem, mach dir keine Sorgen.', '请读：没关系，不要担心。', 'Lies: Kein Problem, mach dir keine Sorgen.', 'hsk1_meiguanxi.mp3'),
    ('hsk1_meiyou', '没有', 'méiyǒu', 'nicht haben / es gibt nicht', '我今天没有时间。', 'Ich habe heute keine Zeit.', '请读：我今天没有时间。', 'Lies: Ich habe heute keine Zeit.', 'hsk1_meiyou.mp3'),
    ('hsk1_mifan', '米饭', 'mǐfàn', 'gekochter Reis', '我喜欢吃米饭。', 'Ich esse gern Reis.', '请读：我喜欢吃米饭。', 'Lies: Ich esse gern Reis.', 'hsk1_mifan.mp3'),
    ('hsk1_mingtian', '明天', 'míngtiān', 'morgen', '明天我去学校。', 'Morgen gehe ich zur Schule.', '请读：明天我去学校。', 'Lies: Morgen gehe ich zur Schule.', 'hsk1_mingtian.mp3'),
    ('hsk1_mingzi', '名字', 'míngzi', 'Name', '你的名字叫什么？', 'Wie heißt du?', '请读：你的名字叫什么？', 'Lies: Wie heißt du?', 'hsk1_mingzi.mp3'),
    ('hsk1_na', '哪', 'nǎ', 'welche / welcher / welches', '你喜欢哪个颜色？', 'Welche Farbe magst du?', '请读：你喜欢哪个颜色？', 'Lies: Welche Farbe magst du?', 'hsk1_na.mp3'),
    ('hsk1_nar', '哪儿', 'nǎr', 'wo', '你要去哪儿？', 'Wohin gehst du?', '请读：你要去哪儿？', 'Lies: Wohin gehst du?', 'hsk1_nar.mp3'),
    ('hsk1_na2', '那', 'nà', 'das / jenes', '那是我的书。', 'Das ist mein Buch.', '请读：那是我的书。', 'Lies: Das ist mein Buch.', 'hsk1_na2.mp3'),
    ('hsk1_ne', '呢', 'ne', 'Fragepartikel / und?', '我很好，你呢？', "Mir geht's gut, und dir?", '请读：我很好，你呢？', "Lies: Mir geht's gut, und dir?", 'hsk1_ne.mp3'),
    ('hsk1_neng', '能', 'néng', 'können / imstande sein', '我能来。', 'Ich kann kommen.', '请读：我能来。', 'Lies: Ich kann kommen.', 'hsk1_neng.mp3'),
    ('hsk1_ni', '你', 'nǐ', 'du / dich', '你好！你叫什么名字？', 'Hallo! Wie heißt du?', '请读：你好！你叫什么名字？', 'Lies: Hallo! Wie heißt du?', 'hsk1_ni.mp3'),
    ('hsk1_nian', '年', 'nián', 'Jahr', '今年我二十岁。', 'Dieses Jahr bin ich zwanzig Jahre alt.', '请读：今年我二十岁。', 'Lies: Dieses Jahr bin ich zwanzig Jahre alt.', 'hsk1_nian.mp3'),
    ('hsk1_nuer', '女儿', 'nǚér', 'Tochter', '他有一个可爱的女儿。', 'Er hat eine niedliche Tochter.', '请读：他有一个可爱的女儿。', 'Lies: Er hat eine niedliche Tochter.', 'hsk1_nuer.mp3'),
    ('hsk1_pengyou', '朋友', 'péngyou', 'Freund / Freundin', '他是我的好朋友。', 'Er ist mein guter Freund.', '请读：他是我的好朋友。', 'Lies: Er ist mein guter Freund.', 'hsk1_pengyou.mp3'),
    ('hsk1_piaoliang', '漂亮', 'piàoliang', 'schön / hübsch', '这朵花很漂亮。', 'Diese Blume ist sehr schön.', '请读：这朵花很漂亮。', 'Lies: Diese Blume ist sehr schön.', 'hsk1_piaoliang.mp3'),
    ('hsk1_pingguo', '苹果', 'píngguǒ', 'Apfel', '我每天吃一个苹果。', 'Ich esse jeden Tag einen Apfel.', '请读：我每天吃一个苹果。', 'Lies: Ich esse jeden Tag einen Apfel.', 'hsk1_pingguo.mp3'),
    ('hsk1_qi', '七', 'qī', 'sieben', '一个星期有七天。', 'Eine Woche hat sieben Tage.', '请读：一个星期有七天。', 'Lies: Eine Woche hat sieben Tage.', 'hsk1_qi.mp3'),
    ('hsk1_qian', '钱', 'qián', 'Geld', '你有多少钱？', 'Wie viel Geld hast du?', '请读：你有多少钱？', 'Lies: Wie viel Geld hast du?', 'hsk1_qian.mp3'),
    ('hsk1_qianmian', '前面', 'qiánmiàn', 'vorne / vor', '学校就在前面。', 'Die Schule ist gleich da vorne.', '请读：学校就在前面。', 'Lies: Die Schule ist gleich da vorne.', 'hsk1_qianmian.mp3'),
    ('hsk1_qing', '请', 'qǐng', 'bitte / einladen', '请坐！', 'Bitte setz dich!', '请读：请坐！', 'Lies: Bitte setz dich!', 'hsk1_qing.mp3'),
    ('hsk1_qu', '去', 'qù', 'gehen / fahren', '我们去北京旅游。', 'Wir reisen nach Peking.', '请读：我们去北京旅游。', 'Lies: Wir reisen nach Peking.', 'hsk1_qu.mp3'),
    ('hsk1_re', '热', 'rè', 'heiß', '今天天气很热。', 'Das Wetter ist heute sehr heiß.', '请读：今天天气很热。', 'Lies: Das Wetter ist heute sehr heiß.', 'hsk1_re.mp3'),
    ('hsk1_ren', '人', 'rén', 'Mensch / Leute', '这里有很多人。', 'Hier sind viele Leute.', '请读：这里有很多人。', 'Lies: Hier sind viele Leute.', 'hsk1_ren.mp3'),
    ('hsk1_renshi', '认识', 'rènshi', 'kennen / erkennen', '我认识他。', 'Ich kenne ihn.', '请读：我认识他。', 'Lies: Ich kenne ihn.', 'hsk1_renshi.mp3'),
    ('hsk1_san', '三', 'sān', 'drei', '我家有三口人。', 'In meiner Familie gibt es drei Personen.', '请读：我家有三口人。', 'Lies: In meiner Familie gibt es drei Personen.', 'hsk1_san.mp3'),
    ('hsk1_shangdian', '商店', 'shāngdiàn', 'Geschäft / Laden', '商店几点开门？', 'Wann öffnet das Geschäft?', '请读：商店几点开门？', 'Lies: Wann öffnet das Geschäft?', 'hsk1_shangdian.mp3'),
    ('hsk1_shang', '上', 'shàng', 'auf / oben', '书在桌子上。', 'Das Buch liegt auf dem Tisch.', '请读：书在桌子上。', 'Lies: Das Buch liegt auf dem Tisch.', 'hsk1_shang.mp3'),
    ('hsk1_shangwu', '上午', 'shàngwǔ', 'Vormittag', '我上午去学校上课。', 'Ich gehe am Vormittag zum Unterricht in die Schule.', '请读：我上午去学校上课。', 'Lies: Ich gehe am Vormittag zur Schule.', 'hsk1_shangwu.mp3'),
    ('hsk1_shao', '少', 'shǎo', 'wenig / wenige', '这里人很少，很安静。', 'Hier sind nur wenige Leute, es ist sehr ruhig.', '请读：这里人很少，很安静。', 'Lies: Hier sind nur wenige Leute, es ist sehr ruhig.', 'hsk1_shao.mp3'),
    ('hsk1_shei', '谁', 'shéi', 'wer', '那个人是谁？', 'Wer ist diese Person?', '请读：那个人是谁？', 'Lies: Wer ist diese Person?', 'hsk1_shei.mp3'),
    ('hsk1_shenme', '什么', 'shénme', 'was', '你想吃什么？', 'Was möchtest du essen?', '请读：你想吃什么？', 'Lies: Was möchtest du essen?', 'hsk1_shenme.mp3'),
    ('hsk1_shi2', '十', 'shí', 'zehn', '我有十个苹果。', 'Ich habe zehn Äpfel.', '请读：我有十个苹果。', 'Lies: Ich habe zehn Äpfel.', 'hsk1_shi2.mp3'),
    ('hsk1_shihou', '时候', 'shíhòu', 'Zeitpunkt / Zeit', '你什么时候来我家？', 'Wann kommst du zu mir nach Hause?', '请读：你什么时候来我家？', 'Lies: Wann kommst du zu mir nach Hause?', 'hsk1_shihou.mp3'),
    ('hsk1_shi', '是', 'shì', 'sein', '我是学生。', 'Ich bin Schüler.', '请读：我是学生。', 'Lies: Ich bin Schüler.', 'hsk1_shi.mp3'),
    ('hsk1_shu', '书', 'shū', 'Buch', '这本书很有意思。', 'Dieses Buch ist sehr interessant.', '请读：这本书很有意思。', 'Lies: Dieses Buch ist sehr interessant.', 'hsk1_shu.mp3'),
    ('hsk1_shui', '水', 'shuǐ', 'Wasser', '请给我一杯水。', 'Bitte gib mir ein Glas Wasser.', '请读：请给我一杯水。', 'Lies: Bitte gib mir ein Glas Wasser.', 'hsk1_shui.mp3'),
    ('hsk1_shuiguo', '水果', 'shuǐguǒ', 'Obst', '我每天吃水果，对身体好。', 'Ich esse jeden Tag Obst, das ist gut für die Gesundheit.', '请读：我每天吃水果，对身体好。', 'Lies: Ich esse jeden Tag Obst, das ist gut für die Gesundheit.', 'hsk1_shuiguo.mp3'),
    ('hsk1_shuijiao', '睡觉', 'shuìjiào', 'schlafen', '我每天晚上十一点睡觉。', 'Ich gehe jeden Abend um elf Uhr schlafen.', '请读：我每天晚上十一点睡觉。', 'Lies: Ich gehe jeden Abend um elf Uhr schlafen.', 'hsk1_shuijiao.mp3'),
    ('hsk1_shuo', '说', 'shuō', 'sprechen / sagen', '请说慢一点儿。', 'Bitte sprich etwas langsamer.', '请读：请说慢一点儿。', 'Lies: Bitte sprich etwas langsamer.', 'hsk1_shuo.mp3'),
    ('hsk1_si', '四', 'sì', 'vier', '一年有四个季节。', 'Ein Jahr hat vier Jahreszeiten.', '请读：一年有四个季节。', 'Lies: Ein Jahr hat vier Jahreszeiten.', 'hsk1_si.mp3'),
    ('hsk1_sui', '岁', 'suì', 'Jahre alt', '他今年二十五岁了。', 'Er ist dieses Jahr fünfundzwanzig Jahre alt.', '请读：他今年二十五岁了。', 'Lies: Er ist dieses Jahr fünfundzwanzig Jahre alt.', 'hsk1_sui.mp3'),
    ('hsk1_ta', '他', 'tā', 'er / ihn', '他是我的老师。', 'Er ist mein Lehrer.', '请读：他是我的老师。', 'Lies: Er ist mein Lehrer.', 'hsk1_ta.mp3'),
    ('hsk1_ta2', '她', 'tā', 'sie / ihr', '她是我的好朋友。', 'Sie ist meine gute Freundin.', '请读：她是我的好朋友。', 'Lies: Sie ist meine gute Freundin.', 'hsk1_ta2.mp3'),
    ('hsk1_tai', '太', 'tài', 'zu / allzu', '这个太贵了，我买不起。', 'Das ist zu teuer, ich kann es mir nicht leisten.', '请读：这个太贵了，我买不起。', 'Lies: Das ist zu teuer, ich kann es mir nicht leisten.', 'hsk1_tai.mp3'),
    ('hsk1_tianqi', '天气', 'tiānqì', 'Wetter', '今天天气怎么样？', 'Wie ist das Wetter heute?', '请读：今天天气怎么样？', 'Lies: Wie ist das Wetter heute?', 'hsk1_tianqi.mp3'),
    ('hsk1_ting', '听', 'tīng', 'hören', '我喜欢听音乐。', 'Ich höre gern Musik.', '请读：我喜欢听音乐。', 'Lies: Ich höre gern Musik.', 'hsk1_ting.mp3'),
    ('hsk1_tongxue', '同学', 'tóngxué', 'Mitschüler / Mitschülerin', '他是我的同学。', 'Er ist mein Mitschüler.', '请读：他是我的同学。', 'Lies: Er ist mein Mitschüler.', 'hsk1_tongxue.mp3'),
    ('hsk1_wei', '喂', 'wèi', 'hallo (am Telefon)', '喂，你好，请问李老师在吗？', 'Hallo, ist Lehrer Li bitte da?', '请读：喂，你好，请问李老师在吗？', 'Lies: Hallo, ist Lehrer Li bitte da?', 'hsk1_wei.mp3'),
    ('hsk1_wo', '我', 'wǒ', 'ich / mich', '我是一名学生。', 'Ich bin Schüler.', '请读：我是一名学生。', 'Lies: Ich bin Schüler.', 'hsk1_wo.mp3'),
    ('hsk1_women', '我们', 'wǒmen', 'wir / uns', '我们一起去图书馆吧。', 'Lass uns zusammen in die Bibliothek gehen.', '请读：我们一起去图书馆吧。', 'Lies: Lass uns zusammen in die Bibliothek gehen.', 'hsk1_women.mp3'),
    ('hsk1_wu', '五', 'wǔ', 'fünf', '我有五本中文书。', 'Ich habe fünf chinesische Bücher.', '请读：我有五本中文书。', 'Lies: Ich habe fünf chinesische Bücher.', 'hsk1_wu.mp3'),
    ('hsk1_xihuan', '喜欢', 'xǐhuān', 'mögen', '我喜欢中国。', 'Ich mag China.', '请读：我喜欢中国。', 'Lies: Ich mag China.', 'hsk1_xihuan.mp3'),
    ('hsk1_xia', '下', 'xià', 'unter / unten', '猫在桌子下面。', 'Die Katze ist unter dem Tisch.', '请读：猫在桌子下面。', 'Lies: Die Katze ist unter dem Tisch.', 'hsk1_xia.mp3'),
    ('hsk1_xiawu', '下午', 'xiàwǔ', 'Nachmittag', '下午我去图书馆看书。', 'Am Nachmittag gehe ich in die Bibliothek, um zu lesen.', '请读：下午我去图书馆看书。', 'Lies: Am Nachmittag gehe ich in die Bibliothek, um zu lesen.', 'hsk1_xiawu.mp3'),
    ('hsk1_xiayu', '下雨', 'xià yǔ', 'regnen', '今天下雨了，记得带伞。', 'Heute regnet es, vergiss deinen Schirm nicht.', '请读：今天下雨了，记得带伞。', 'Lies: Heute regnet es, vergiss deinen Schirm nicht.', 'hsk1_xiayu.mp3'),
    ('hsk1_xiansheng', '先生', 'xiānshēng', 'Herr / Ehemann', '王先生，您好！', 'Guten Tag, Herr Wang!', '请读：王先生，您好！', 'Lies: Guten Tag, Herr Wang!', 'hsk1_xiansheng.mp3'),
    ('hsk1_xianzai', '现在', 'xiànzài', 'jetzt', '现在几点了？', 'Wie spät ist es jetzt?', '请读：现在几点了？', 'Lies: Wie spät ist es jetzt?', 'hsk1_xianzai.mp3'),
    ('hsk1_xiang', '想', 'xiǎng', 'wollen / denken / vermissen', '我想回家休息。', 'Ich möchte nach Hause gehen und mich ausruhen.', '请读：我想回家休息。', 'Lies: Ich möchte nach Hause gehen und mich ausruhen.', 'hsk1_xiang.mp3'),
    ('hsk1_xiao', '小', 'xiǎo', 'klein', '这个房间很小，只有一张床。', 'Dieses Zimmer ist sehr klein, es gibt nur ein Bett.', '请读：这个房间很小，只有一张床。', 'Lies: Dieses Zimmer ist sehr klein, es gibt nur ein Bett.', 'hsk1_xiao.mp3'),
    ('hsk1_xiaojie', '小姐', 'xiǎojiě', 'junge Dame', '请问，小姐，洗手间在哪里？', 'Entschuldigen Sie, junge Dame, wo ist die Toilette?', '请读：请问，小姐，洗手间在哪里？', 'Lies: Entschuldigen Sie, junge Dame, wo ist die Toilette?', 'hsk1_xiaojie.mp3'),
    ('hsk1_xie', '些', 'xiē', 'einige / ein paar', '我买了一些水果和蔬菜。', 'Ich habe etwas Obst und Gemüse gekauft.', '请读：我买了一些水果和蔬菜。', 'Lies: Ich habe etwas Obst und Gemüse gekauft.', 'hsk1_xie.mp3'),
    ('hsk1_xie2', '写', 'xiě', 'schreiben', '我写汉字。', 'Ich schreibe chinesische Schriftzeichen.', '请读：我写汉字。', 'Lies: Ich schreibe chinesische Schriftzeichen.', 'hsk1_xie2.mp3'),
    ('hsk1_xiexie', '谢谢', 'xièxie', 'danke', '谢谢你的帮助！', 'Danke für deine Hilfe!', '请读：谢谢你的帮助！', 'Lies: Danke für deine Hilfe!', 'hsk1_xiexie.mp3'),
    ('hsk1_xingqi', '星期', 'xīngqī', 'Woche', '这个星期我有很多作业。', 'Diese Woche habe ich viele Hausaufgaben.', '请读：这个星期我有很多作业。', 'Lies: Diese Woche habe ich viele Hausaufgaben.', 'hsk1_xingqi.mp3'),
    ('hsk1_xuesheng', '学生', 'xuéshēng', 'Schüler / Schülerin', '他们都是学生。', 'Sie sind alle Schüler.', '请读：他们都是学生。', 'Lies: Sie sind alle Schüler.', 'hsk1_xuesheng.mp3'),
    ('hsk1_xuexi', '学习', 'xuéxí', 'lernen / studieren', '我每天学习汉语。', 'Ich lerne jeden Tag Chinesisch.', '请读：我每天学习汉语。', 'Lies: Ich lerne jeden Tag Chinesisch.', 'hsk1_xuexi.mp3'),
    ('hsk1_xuexiao', '学校', 'xuéxiào', 'Schule', '学校在我家附近。', 'Die Schule ist in der Nähe meines Hauses.', '请读：学校在我家附近。', 'Lies: Die Schule ist in der Nähe meines Zuhauses.', 'hsk1_xuexiao.mp3'),
    ('hsk1_yi', '一', 'yī', 'eins', '我只有一个苹果。', 'Ich habe nur einen Apfel.', '请读：我只有一个苹果。', 'Lies: Ich habe nur einen Apfel.', 'hsk1_yi.mp3'),
    ('hsk1_yidianr', '一点儿', 'yīdiǎnr', 'ein bisschen', '我会说一点儿汉语。', 'Ich kann ein bisschen Chinesisch sprechen.', '请读：我会说一点儿汉语。', 'Lies: Ich kann ein bisschen Chinesisch sprechen.', 'hsk1_yidianr.mp3'),
    ('hsk1_yifu', '衣服', 'yīfu', 'Kleidung', '我要买一些新衣服。', 'Ich möchte ein paar neue Kleidungsstücke kaufen.', '请读：我要买一些新衣服。', 'Lies: Ich möchte ein paar neue Kleidungsstücke kaufen.', 'hsk1_yifu.mp3'),
    ('hsk1_yisheng', '医生', 'yīshēng', 'Arzt / Ärztin', '我头疼，要去看医生。', 'Ich habe Kopfschmerzen und muss zum Arzt.', '请读：我头疼，要去看医生。', 'Lies: Ich habe Kopfschmerzen und muss zum Arzt.', 'hsk1_yisheng.mp3'),
    ('hsk1_yiyuan', '医院', 'yīyuàn', 'Krankenhaus', '医院在学校旁边。', 'Das Krankenhaus ist neben der Schule.', '请读：医院在学校旁边。', 'Lies: Das Krankenhaus ist neben der Schule.', 'hsk1_yiyuan.mp3'),
    ('hsk1_yizi', '椅子', 'yǐzi', 'Stuhl', '请坐在椅子上等一下。', 'Bitte setz dich auf den Stuhl und warte einen Moment.', '请读：请坐在椅子上等一下。', 'Lies: Bitte setz dich auf den Stuhl und warte einen Moment.', 'hsk1_yizi.mp3'),
    ('hsk1_you', '有', 'yǒu', 'haben / es gibt', '你有兄弟姐妹吗？', 'Hast du Geschwister?', '请读：你有兄弟姐妹吗？', 'Lies: Hast du Geschwister?', 'hsk1_you.mp3'),
    ('hsk1_yue', '月', 'yuè', 'Monat', '一年有十二个月。', 'Ein Jahr hat zwölf Monate.', '请读：一年有十二个月。', 'Lies: Ein Jahr hat zwölf Monate.', 'hsk1_yue.mp3'),
    ('hsk1_zai', '在', 'zài', 'in / an / sich befinden', '他在哪里工作？', 'Wo arbeitet er?', '请读：他在哪里工作？', 'Lies: Wo arbeitet er?', 'hsk1_zai.mp3'),
    ('hsk1_zaijian', '再见', 'zàijiàn', 'auf Wiedersehen', '明天见，再见！', 'Bis morgen, auf Wiedersehen!', '请读：明天见，再见！', 'Lies: Bis morgen, auf Wiedersehen!', 'hsk1_zaijian.mp3'),
    ('hsk1_zenme', '怎么', 'zěnme', 'wie / warum', '这个字怎么写？', 'Wie schreibt man dieses Zeichen?', '请读：这个字怎么写？', 'Lies: Wie schreibt man dieses Zeichen?', 'hsk1_zenme.mp3'),
    ('hsk1_zenmeyang', '怎么样', 'zěnmeyàng', 'wie / wie wäre es / wie ist', '你觉得这个菜怎么样？', 'Wie findest du dieses Gericht?', '请读：你觉得这个菜怎么样？', 'Lies: Wie findest du dieses Gericht?', 'hsk1_zenmeyang.mp3'),
    ('hsk1_zhe', '这', 'zhè', 'dies / das hier', '这是什么？', 'Was ist das?', '请读：这是什么？', 'Lies: Was ist das?', 'hsk1_zhe.mp3'),
    ('hsk1_zhongguo', '中国', 'Zhōngguó', 'China', '我来自中国。', 'Ich komme aus China.', '请读：我来自中国。', 'Lies: Ich komme aus China.', 'hsk1_zhongguo.mp3'),
    ('hsk1_zhongwu', '中午', 'zhōngwǔ', 'Mittag', '中午我们一起去吃饭吧。', 'Lass uns heute Mittag zusammen essen gehen.', '请读：中午我们一起去吃饭吧。', 'Lies: Lass uns heute Mittag zusammen essen gehen.', 'hsk1_zhongwu.mp3'),
    ('hsk1_zhu', '住', 'zhù', 'wohnen', '你住在哪里？', 'Wo wohnst du?', '请读：你住在哪里？', 'Lies: Wo wohnst du?', 'hsk1_zhu.mp3'),
    ('hsk1_zhuozi', '桌子', 'zhuōzi', 'Tisch', '书放在桌子上。', 'Leg das Buch auf den Tisch.', '请读：书放在桌子上。', 'Lies: Leg das Buch auf den Tisch.', 'hsk1_zhuozi.mp3'),
    ('hsk1_zi', '字', 'zì', 'Zeichen / Schriftzeichen', '这个字怎么写？', 'Wie schreibt man dieses Zeichen?', '请读：这个字怎么写？', 'Lies: Wie schreibt man dieses Zeichen?', 'hsk1_zi.mp3'),
    ('hsk1_zuotian', '昨天', 'zuótiān', 'gestern', '昨天我见了一个老朋友。', 'Gestern habe ich einen alten Freund getroffen.', '请读：昨天我见了一个老朋友。', 'Lies: Gestern habe ich einen alten Freund getroffen.', 'hsk1_zuotian.mp3'),
    ('hsk1_zuo2', '坐', 'zuò', 'sitzen', '请坐。', 'Bitte setz dich.', '请读：请坐。', 'Lies: Bitte setz dich.', 'hsk1_zuo2.mp3'),
    ('hsk1_zuo', '做', 'zuò', 'machen / tun', '我做饭。', 'Ich koche.', '请读：我做饭。', 'Lies: Ich koche.', 'hsk1_zuo.mp3'),
]

AUDIO_SENTENCE_PINYIN = {
    'hsk1_ai': 'Wǒ ài wǒ de jiārén.',
    'hsk1_ba2': 'Wǒ yǒu bā běn shū.',
    'hsk1_ba': 'Wǒ bàba zài jiā gōngzuò.',
    'hsk1_beizi': 'Qǐng gěi wǒ yīgè bēizi.',
    'hsk1_beijing': 'Běijīng shì Zhōngguó de shǒudū.',
    'hsk1_ben': 'Wǒ mǎi le sān běn shū.',
    'hsk1_bukeqi': 'Xièxie nǐ! Bù kèqi.',
    'hsk1_bu': 'Wǒ bù hē kāfēi, wǒ hē chá.',
    'hsk1_cai': 'Zhè dào cài hěn hǎochī.',
    'hsk1_cha': 'Wǒ měitiān hē chá.',
    'hsk1_chi': 'Wǒ xǐhuān chī mǐfàn.',
    'hsk1_chuzuche': 'Wǒ zuò chūzūchē qù jīchǎng.',
    'hsk1_dadianhua': 'Wǒ gěi māma dǎ diànhuà.',
    'hsk1_da': 'Zhège píngguǒ hěn dà.',
    'hsk1_de': 'Zhè shì wǒ de shū.',
    'hsk1_dian': 'Xiànzài shì sān diǎn.',
    'hsk1_diannao': 'Tā yòng diànnǎo gōngzuò.',
    'hsk1_dianshi': 'Wǒ měitiān wǎnshàng kàn diànshì.',
    'hsk1_dianying': 'Wǒ zhōumò xǐhuān kàn diànyǐng.',
    'hsk1_dongxi': 'Nǐ mǎi le shénme dōngxi?',
    'hsk1_dou': 'Wǒmen dōu shì xuéshēng.',
    'hsk1_du': 'Wǒ dú shū.',
    'hsk1_duibuqi': 'Duìbuqǐ, wǒ lái wǎn le.',
    'hsk1_duo': 'Zhèlǐ yǒu hěn duō rén.',
    'hsk1_duoshao': 'Zhège duōshao qián?',
    'hsk1_erzi': 'Tā yǒu yīgè cōngming de érzi.',
    'hsk1_er': 'Wǒ yǒu liǎng gè gēgē.',
    'hsk1_fandian': 'Zhè jiā fàndiàn hěn hǎo.',
    'hsk1_feiji': 'Wǒ zuò fēijī qù Shànghǎi.',
    'hsk1_fenzhong': 'Qǐng děng wǒ wǔ fēnzhōng.',
    'hsk1_gaoxing': 'Jiàn dào nǐ wǒ hěn gāoxìng.',
    'hsk1_ge': 'Qǐng gěi wǒ yīgè píngguǒ.',
    'hsk1_gongzuo': 'Tā zài yínháng gōngzuò.',
    'hsk1_gou': 'Wǒ jiā yǒu yī zhī gǒu.',
    'hsk1_hanyu': 'Wǒ zài xuéxí Hànyǔ.',
    'hsk1_hao': 'Jīntiān tiānqì hěn hǎo.',
    'hsk1_hao2': 'Jīntiān jǐ hào?',
    'hsk1_he': 'Wǒ xiǎng hē yī bēi chá.',
    'hsk1_he2': 'Wǒ hé nǐ shì péngyou.',
    'hsk1_hen': 'Wǒ jīntiān hěn gāoxìng.',
    'hsk1_houmian': 'Tā zài wǒ hòumiàn.',
    'hsk1_hui2': 'Wǒ xiàwǔ huí jiā.',
    'hsk1_hui': 'Wǒ huì shuō yīdiǎn Hànyǔ.',
    'hsk1_ji': 'Nǐ yǒu jǐ gè péngyou?',
    'hsk1_jia': 'Wǒ jiā zài Běijīng fùjìn.',
    'hsk1_jiao': 'Wǒ jiào Xiǎo Míng.',
    'hsk1_jintian': 'Jīntiān shì xīngqī jǐ?',
    'hsk1_jiu': 'Yīgè yuè yǒu sānshí tiān, wǒ gōngzuò le jiǔ tiān.',
    'hsk1_kai': 'Qǐng kāi mén.',
    'hsk1_kan': 'Wǒmen yīqǐ kàn shū ba.',
    'hsk1_kanjian': 'Wǒ kànjiàn tā le.',
    'hsk1_kuai': 'Zhège píngguǒ yī kuài qián.',
    'hsk1_lai': 'Qǐng nǐ lái wǒ jiā chīfàn.',
    'hsk1_laoshi': 'Wǒ de lǎoshī hěn hǎo.',
    'hsk1_le': 'Wǒ chī le zǎofàn.',
    'hsk1_leng': 'Jīntiān hěn lěng.',
    'hsk1_li': 'Shūbāo lǐ yǒu hěn duō shū.',
    'hsk1_liu': 'Yīgè xīngqī yǒu qī tiān, wǒ shàng le liù tiān kè.',
    'hsk1_mama': 'Wǒ māma zài jiā zuòfàn.',
    'hsk1_ma': 'Nǐ xǐhuān chī jiǎozi ma?',
    'hsk1_mai': 'Wǒ mǎi le yī běn shū.',
    'hsk1_mao': 'Wǒ yǒu yī zhī māo.',
    'hsk1_meiguanxi': 'Méi guānxi, bùyào dānxīn.',
    'hsk1_meiyou': 'Wǒ jīntiān méiyǒu shíjiān.',
    'hsk1_mifan': 'Wǒ xǐhuān chī mǐfàn.',
    'hsk1_mingtian': 'Míngtiān wǒ qù xuéxiào.',
    'hsk1_mingzi': 'Nǐ de míngzi jiào shénme?',
    'hsk1_na': 'Nǐ xǐhuān nǎ gè yánsè?',
    'hsk1_nar': 'Nǐ yào qù nǎr?',
    'hsk1_na2': 'Nà shì wǒ de shū.',
    'hsk1_ne': 'Wǒ hěn hǎo, nǐ ne?',
    'hsk1_neng': 'Wǒ néng lái.',
    'hsk1_ni': 'Nǐ hǎo! Nǐ jiào shénme míngzi?',
    'hsk1_nian': 'Jīnnián wǒ èrshí suì.',
    'hsk1_nuer': "Tā yǒu yīgè kě'ài de nǚér.",
    'hsk1_pengyou': 'Tā shì wǒ de hǎo péngyou.',
    'hsk1_piaoliang': 'Zhè duǒ huā hěn piàoliang.',
    'hsk1_pingguo': 'Wǒ měitiān chī yīgè píngguǒ.',
    'hsk1_qi': 'Yīgè xīngqī yǒu qī tiān.',
    'hsk1_qian': 'Nǐ yǒu duōshao qián?',
    'hsk1_qianmian': 'Xuéxiào jiù zài qiánmiàn.',
    'hsk1_qing': 'Qǐng zuò!',
    'hsk1_qu': 'Wǒmen qù Běijīng lǚyóu.',
    'hsk1_re': 'Jīntiān tiānqì hěn rè.',
    'hsk1_ren': 'Zhèlǐ yǒu hěn duō rén.',
    'hsk1_renshi': 'Wǒ rènshi tā.',
    'hsk1_san': 'Wǒ jiā yǒu sān kǒu rén.',
    'hsk1_shangdian': 'Shāngdiàn jǐ diǎn kāimén?',
    'hsk1_shang': 'Shū zài zhuōzi shàng.',
    'hsk1_shangwu': 'Wǒ shàngwǔ qù xuéxiào shàngkè.',
    'hsk1_shao': 'Zhèlǐ rén hěn shǎo, hěn ānjìng.',
    'hsk1_shei': 'Nà gè rén shì shéi?',
    'hsk1_shenme': 'Nǐ xiǎng chī shénme?',
    'hsk1_shi2': 'Wǒ yǒu shí gè píngguǒ.',
    'hsk1_shihou': 'Nǐ shénme shíhòu lái wǒ jiā?',
    'hsk1_shi': 'Wǒ shì xuéshēng.',
    'hsk1_shu': 'Zhè běn shū hěn yǒuyìsi.',
    'hsk1_shui': 'Qǐng gěi wǒ yī bēi shuǐ.',
    'hsk1_shuiguo': 'Wǒ měitiān chī shuǐguǒ, duì shēntǐ hǎo.',
    'hsk1_shuijiao': 'Wǒ měitiān wǎnshàng shíyī diǎn shuìjiào.',
    'hsk1_shuo': 'Qǐng shuō màn yīdiǎnr.',
    'hsk1_si': 'Yī nián yǒu sì gè jìjié.',
    'hsk1_sui': 'Tā jīnnián èrshíwǔ suì le.',
    'hsk1_ta': 'Tā shì wǒ de lǎoshī.',
    'hsk1_ta2': 'Tā shì wǒ de hǎo péngyou.',
    'hsk1_tai': 'Zhège tài guì le, wǒ mǎi bu qǐ.',
    'hsk1_tianqi': 'Jīntiān tiānqì zěnmeyàng?',
    'hsk1_ting': 'Wǒ xǐhuān tīng yīnyuè.',
    'hsk1_tongxue': 'Tā shì wǒ de tóngxué.',
    'hsk1_wei': 'Wèi, nǐ hǎo, qǐngwèn Lǐ lǎoshī zài ma?',
    'hsk1_wo': 'Wǒ shì yī míng xuéshēng.',
    'hsk1_women': 'Wǒmen yīqǐ qù túshūguǎn ba.',
    'hsk1_wu': 'Wǒ yǒu wǔ běn Zhōngwén shū.',
    'hsk1_xihuan': 'Wǒ xǐhuān Zhōngguó.',
    'hsk1_xia': 'Māo zài zhuōzi xiàmiàn.',
    'hsk1_xiawu': 'Xiàwǔ wǒ qù túshūguǎn kàn shū.',
    'hsk1_xiayu': 'Jīntiān xià yǔ le, jìde dài sǎn.',
    'hsk1_xiansheng': 'Wáng xiānshēng, nín hǎo!',
    'hsk1_xianzai': 'Xiànzài jǐ diǎn le?',
    'hsk1_xiang': 'Wǒ xiǎng huí jiā xiūxi.',
    'hsk1_xiao': 'Zhège fángjiān hěn xiǎo, zhǐ yǒu yī zhāng chuáng.',
    'hsk1_xiaojie': 'Qǐngwèn, xiǎojiě, xǐshǒujiān zài nǎlǐ?',
    'hsk1_xie': 'Wǒ mǎi le yīxiē shuǐguǒ hé shūcài.',
    'hsk1_xie2': 'Wǒ xiě Hànzì.',
    'hsk1_xiexie': 'Xièxie nǐ de bāngzhù!',
    'hsk1_xingqi': 'Zhège xīngqī wǒ yǒu hěn duō zuòyè.',
    'hsk1_xuesheng': 'Tāmen dōu shì xuéshēng.',
    'hsk1_xuexi': 'Wǒ měitiān xuéxí Hànyǔ.',
    'hsk1_xuexiao': 'Xuéxiào zài wǒ jiā fùjìn.',
    'hsk1_yi': 'Wǒ zhǐ yǒu yīgè píngguǒ.',
    'hsk1_yidianr': 'Wǒ huì shuō yīdiǎnr Hànyǔ.',
    'hsk1_yifu': 'Wǒ yào mǎi yīxiē xīn yīfu.',
    'hsk1_yisheng': 'Wǒ tóuténg, yào qù kàn yīshēng.',
    'hsk1_yiyuan': 'Yīyuàn zài xuéxiào pángbiān.',
    'hsk1_yizi': 'Qǐng zuò zài yǐzi shàng děng yīxià.',
    'hsk1_you': 'Nǐ yǒu xiōngdì jiěmèi ma?',
    'hsk1_yue': "Yī nián yǒu shí'èr gè yuè.",
    'hsk1_zai': 'Tā zài nǎlǐ gōngzuò?',
    'hsk1_zaijian': 'Míngtiān jiàn, zàijiàn!',
    'hsk1_zenme': 'Zhège zì zěnme xiě?',
    'hsk1_zenmeyang': 'Nǐ juéde zhège cài zěnmeyàng?',
    'hsk1_zhe': 'Zhè shì shénme?',
    'hsk1_zhongguo': 'Wǒ lái zì Zhōngguó.',
    'hsk1_zhongwu': 'Zhōngwǔ wǒmen yīqǐ qù chīfàn ba.',
    'hsk1_zhu': 'Nǐ zhù zài nǎlǐ?',
    'hsk1_zhuozi': 'Shū fàng zài zhuōzi shàng.',
    'hsk1_zi': 'Zhège zì zěnme xiě?',
    'hsk1_zuotian': 'Zuótiān wǒ jiàn le yīgè lǎo péngyou.',
    'hsk1_zuo2': 'Qǐng zuò.',
    'hsk1_zuo': 'Wǒ zuò fàn.',
}

READING_SENTENCE_PINYIN = {
    'hsk1_ai': 'Qǐng dú：Wǒ ài wǒ de jiārén.',
    'hsk1_ba2': 'Qǐng dú：Wǒ yǒu bā běn shū.',
    'hsk1_ba': 'Qǐng dú：Wǒ bàba zài jiā gōngzuò.',
    'hsk1_beizi': 'Qǐng dú：Qǐng gěi wǒ yīgè bēizi.',
    'hsk1_beijing': 'Qǐng dú：Běijīng shì Zhōngguó de shǒudū.',
    'hsk1_ben': 'Qǐng dú：Wǒ mǎi le sān běn shū.',
    'hsk1_bukeqi': 'Qǐng dú：Xièxie nǐ! Bù kèqi.',
    'hsk1_bu': 'Qǐng dú：Wǒ bù hē kāfēi, wǒ hē chá.',
    'hsk1_cai': 'Qǐng dú：Zhè dào cài hěn hǎochī.',
    'hsk1_cha': 'Qǐng dú：Wǒ měitiān hē chá.',
    'hsk1_chi': 'Qǐng dú：Wǒ xǐhuān chī mǐfàn.',
    'hsk1_chuzuche': 'Qǐng dú：Wǒ zuò chūzūchē qù jīchǎng.',
    'hsk1_dadianhua': 'Qǐng dú：Wǒ gěi māma dǎ diànhuà.',
    'hsk1_da': 'Qǐng dú：Zhège píngguǒ hěn dà.',
    'hsk1_de': 'Qǐng dú：Zhè shì wǒ de shū.',
    'hsk1_dian': 'Qǐng dú：Xiànzài shì sān diǎn.',
    'hsk1_diannao': 'Qǐng dú：Tā yòng diànnǎo gōngzuò.',
    'hsk1_dianshi': 'Qǐng dú：Wǒ měitiān wǎnshàng kàn diànshì.',
    'hsk1_dianying': 'Qǐng dú：Wǒ zhōumò xǐhuān kàn diànyǐng.',
    'hsk1_dongxi': 'Qǐng dú：Nǐ mǎi le shénme dōngxi?',
    'hsk1_dou': 'Qǐng dú：Wǒmen dōu shì xuéshēng.',
    'hsk1_du': 'Qǐng dú：Wǒ dú shū.',
    'hsk1_duibuqi': 'Qǐng dú：Duìbuqǐ, wǒ lái wǎn le.',
    'hsk1_duo': 'Qǐng dú：Zhèlǐ yǒu hěn duō rén.',
    'hsk1_duoshao': 'Qǐng dú：Zhège duōshao qián?',
    'hsk1_erzi': 'Qǐng dú：Tā yǒu yīgè cōngming de érzi.',
    'hsk1_er': 'Qǐng dú：Wǒ yǒu liǎng gè gēgē.',
    'hsk1_fandian': 'Qǐng dú：Zhè jiā fàndiàn hěn hǎo.',
    'hsk1_feiji': 'Qǐng dú：Wǒ zuò fēijī qù Shànghǎi.',
    'hsk1_fenzhong': 'Qǐng dú：Qǐng děng wǒ wǔ fēnzhōng.',
    'hsk1_gaoxing': 'Qǐng dú：Jiàn dào nǐ wǒ hěn gāoxìng.',
    'hsk1_ge': 'Qǐng dú：Qǐng gěi wǒ yīgè píngguǒ.',
    'hsk1_gongzuo': 'Qǐng dú：Tā zài yínháng gōngzuò.',
    'hsk1_gou': 'Qǐng dú：Wǒ jiā yǒu yī zhī gǒu.',
    'hsk1_hanyu': 'Qǐng dú：Wǒ zài xuéxí Hànyǔ.',
    'hsk1_hao': 'Qǐng dú：Jīntiān tiānqì hěn hǎo.',
    'hsk1_hao2': 'Qǐng dú：Jīntiān jǐ hào?',
    'hsk1_he': 'Qǐng dú：Wǒ xiǎng hē yī bēi chá.',
    'hsk1_he2': 'Qǐng dú：Wǒ hé nǐ shì péngyou.',
    'hsk1_hen': 'Qǐng dú：Wǒ jīntiān hěn gāoxìng.',
    'hsk1_houmian': 'Qǐng dú：Tā zài wǒ hòumiàn.',
    'hsk1_hui2': 'Qǐng dú：Wǒ xiàwǔ huí jiā.',
    'hsk1_hui': 'Qǐng dú：Wǒ huì shuō yīdiǎn Hànyǔ.',
    'hsk1_ji': 'Qǐng dú：Nǐ yǒu jǐ gè péngyou?',
    'hsk1_jia': 'Qǐng dú：Wǒ jiā zài Běijīng fùjìn.',
    'hsk1_jiao': 'Qǐng dú：Wǒ jiào Xiǎo Míng.',
    'hsk1_jintian': 'Qǐng dú：Jīntiān shì xīngqī jǐ?',
    'hsk1_jiu': 'Qǐng dú：Yīgè yuè yǒu sānshí tiān, wǒ gōngzuò le jiǔ tiān.',
    'hsk1_kai': 'Qǐng dú：Qǐng kāi mén.',
    'hsk1_kan': 'Qǐng dú：Wǒmen yīqǐ kàn shū ba.',
    'hsk1_kanjian': 'Qǐng dú：Wǒ kànjiàn tā le.',
    'hsk1_kuai': 'Qǐng dú：Zhège píngguǒ yī kuài qián.',
    'hsk1_lai': 'Qǐng dú：Qǐng nǐ lái wǒ jiā chīfàn.',
    'hsk1_laoshi': 'Qǐng dú：Wǒ de lǎoshī hěn hǎo.',
    'hsk1_le': 'Qǐng dú：Wǒ chī le zǎofàn.',
    'hsk1_leng': 'Qǐng dú：Jīntiān hěn lěng.',
    'hsk1_li': 'Qǐng dú：Shūbāo lǐ yǒu hěn duō shū.',
    'hsk1_liu': 'Qǐng dú：Yīgè xīngqī yǒu qī tiān, wǒ shàng le liù tiān kè.',
    'hsk1_mama': 'Qǐng dú：Wǒ māma zài jiā zuòfàn.',
    'hsk1_ma': 'Qǐng dú：Nǐ xǐhuān chī jiǎozi ma?',
    'hsk1_mai': 'Qǐng dú：Wǒ mǎi le yī běn shū.',
    'hsk1_mao': 'Qǐng dú：Wǒ yǒu yī zhī māo.',
    'hsk1_meiguanxi': 'Qǐng dú：Méi guānxi, bùyào dānxīn.',
    'hsk1_meiyou': 'Qǐng dú：Wǒ jīntiān méiyǒu shíjiān.',
    'hsk1_mifan': 'Qǐng dú：Wǒ xǐhuān chī mǐfàn.',
    'hsk1_mingtian': 'Qǐng dú：Míngtiān wǒ qù xuéxiào.',
    'hsk1_mingzi': 'Qǐng dú：Nǐ de míngzi jiào shénme?',
    'hsk1_na': 'Qǐng dú：Nǐ xǐhuān nǎ gè yánsè?',
    'hsk1_nar': 'Qǐng dú：Nǐ yào qù nǎr?',
    'hsk1_na2': 'Qǐng dú：Nà shì wǒ de shū.',
    'hsk1_ne': 'Qǐng dú：Wǒ hěn hǎo, nǐ ne?',
    'hsk1_neng': 'Qǐng dú：Wǒ néng lái.',
    'hsk1_ni': 'Qǐng dú：Nǐ hǎo! Nǐ jiào shénme míngzi?',
    'hsk1_nian': 'Qǐng dú：Jīnnián wǒ èrshí suì.',
    'hsk1_nuer': "Qǐng dú：Tā yǒu yīgè kě'ài de nǚér.",
    'hsk1_pengyou': 'Qǐng dú：Tā shì wǒ de hǎo péngyou.',
    'hsk1_piaoliang': 'Qǐng dú：Zhè duǒ huā hěn piàoliang.',
    'hsk1_pingguo': 'Qǐng dú：Wǒ měitiān chī yīgè píngguǒ.',
    'hsk1_qi': 'Qǐng dú：Yīgè xīngqī yǒu qī tiān.',
    'hsk1_qian': 'Qǐng dú：Nǐ yǒu duōshao qián?',
    'hsk1_qianmian': 'Qǐng dú：Xuéxiào jiù zài qiánmiàn.',
    'hsk1_qing': 'Qǐng dú：Qǐng zuò!',
    'hsk1_qu': 'Qǐng dú：Wǒmen qù Běijīng lǚyóu.',
    'hsk1_re': 'Qǐng dú：Jīntiān tiānqì hěn rè.',
    'hsk1_ren': 'Qǐng dú：Zhèlǐ yǒu hěn duō rén.',
    'hsk1_renshi': 'Qǐng dú：Wǒ rènshi tā.',
    'hsk1_san': 'Qǐng dú：Wǒ jiā yǒu sān kǒu rén.',
    'hsk1_shangdian': 'Qǐng dú：Shāngdiàn jǐ diǎn kāimén?',
    'hsk1_shang': 'Qǐng dú：Shū zài zhuōzi shàng.',
    'hsk1_shangwu': 'Qǐng dú：Wǒ shàngwǔ qù xuéxiào shàngkè.',
    'hsk1_shao': 'Qǐng dú：Zhèlǐ rén hěn shǎo, hěn ānjìng.',
    'hsk1_shei': 'Qǐng dú：Nà gè rén shì shéi?',
    'hsk1_shenme': 'Qǐng dú：Nǐ xiǎng chī shénme?',
    'hsk1_shi2': 'Qǐng dú：Wǒ yǒu shí gè píngguǒ.',
    'hsk1_shihou': 'Qǐng dú：Nǐ shénme shíhòu lái wǒ jiā?',
    'hsk1_shi': 'Qǐng dú：Wǒ shì xuéshēng.',
    'hsk1_shu': 'Qǐng dú：Zhè běn shū hěn yǒuyìsi.',
    'hsk1_shui': 'Qǐng dú：Qǐng gěi wǒ yī bēi shuǐ.',
    'hsk1_shuiguo': 'Qǐng dú：Wǒ měitiān chī shuǐguǒ, duì shēntǐ hǎo.',
    'hsk1_shuijiao': 'Qǐng dú：Wǒ měitiān wǎnshàng shíyī diǎn shuìjiào.',
    'hsk1_shuo': 'Qǐng dú：Qǐng shuō màn yīdiǎnr.',
    'hsk1_si': 'Qǐng dú：Yī nián yǒu sì gè jìjié.',
    'hsk1_sui': 'Qǐng dú：Tā jīnnián èrshíwǔ suì le.',
    'hsk1_ta': 'Qǐng dú：Tā shì wǒ de lǎoshī.',
    'hsk1_ta2': 'Qǐng dú：Tā shì wǒ de hǎo péngyou.',
    'hsk1_tai': 'Qǐng dú：Zhège tài guì le, wǒ mǎi bu qǐ.',
    'hsk1_tianqi': 'Qǐng dú：Jīntiān tiānqì zěnmeyàng?',
    'hsk1_ting': 'Qǐng dú：Wǒ xǐhuān tīng yīnyuè.',
    'hsk1_tongxue': 'Qǐng dú：Tā shì wǒ de tóngxué.',
    'hsk1_wei': 'Qǐng dú：Wèi, nǐ hǎo, qǐngwèn Lǐ lǎoshī zài ma?',
    'hsk1_wo': 'Qǐng dú：Wǒ shì yī míng xuéshēng.',
    'hsk1_women': 'Qǐng dú：Wǒmen yīqǐ qù túshūguǎn ba.',
    'hsk1_wu': 'Qǐng dú：Wǒ yǒu wǔ běn Zhōngwén shū.',
    'hsk1_xihuan': 'Qǐng dú：Wǒ xǐhuān Zhōngguó.',
    'hsk1_xia': 'Qǐng dú：Māo zài zhuōzi xiàmiàn.',
    'hsk1_xiawu': 'Qǐng dú：Xiàwǔ wǒ qù túshūguǎn kàn shū.',
    'hsk1_xiayu': 'Qǐng dú：Jīntiān xià yǔ le, jìde dài sǎn.',
    'hsk1_xiansheng': 'Qǐng dú：Wáng xiānshēng, nín hǎo!',
    'hsk1_xianzai': 'Qǐng dú：Xiànzài jǐ diǎn le?',
    'hsk1_xiang': 'Qǐng dú：Wǒ xiǎng huí jiā xiūxi.',
    'hsk1_xiao': 'Qǐng dú：Zhège fángjiān hěn xiǎo, zhǐ yǒu yī zhāng chuáng.',
    'hsk1_xiaojie': 'Qǐng dú：Qǐngwèn, xiǎojiě, xǐshǒujiān zài nǎlǐ?',
    'hsk1_xie': 'Qǐng dú：Wǒ mǎi le yīxiē shuǐguǒ hé shūcài.',
    'hsk1_xie2': 'Qǐng dú：Wǒ xiě Hànzì.',
    'hsk1_xiexie': 'Qǐng dú：Xièxie nǐ de bāngzhù!',
    'hsk1_xingqi': 'Qǐng dú：Zhège xīngqī wǒ yǒu hěn duō zuòyè.',
    'hsk1_xuesheng': 'Qǐng dú：Tāmen dōu shì xuéshēng.',
    'hsk1_xuexi': 'Qǐng dú：Wǒ měitiān xuéxí Hànyǔ.',
    'hsk1_xuexiao': 'Qǐng dú：Xuéxiào zài wǒ jiā fùjìn.',
    'hsk1_yi': 'Qǐng dú：Wǒ zhǐ yǒu yīgè píngguǒ.',
    'hsk1_yidianr': 'Qǐng dú：Wǒ huì shuō yīdiǎnr Hànyǔ.',
    'hsk1_yifu': 'Qǐng dú：Wǒ yào mǎi yīxiē xīn yīfu.',
    'hsk1_yisheng': 'Qǐng dú：Wǒ tóuténg, yào qù kàn yīshēng.',
    'hsk1_yiyuan': 'Qǐng dú：Yīyuàn zài xuéxiào pángbiān.',
    'hsk1_yizi': 'Qǐng dú：Qǐng zuò zài yǐzi shàng děng yīxià.',
    'hsk1_you': 'Qǐng dú：Nǐ yǒu xiōngdì jiěmèi ma?',
    'hsk1_yue': "Qǐng dú：Yī nián yǒu shí'èr gè yuè.",
    'hsk1_zai': 'Qǐng dú：Tā zài nǎlǐ gōngzuò?',
    'hsk1_zaijian': 'Qǐng dú：Míngtiān jiàn, zàijiàn!',
    'hsk1_zenme': 'Qǐng dú：Zhège zì zěnme xiě?',
    'hsk1_zenmeyang': 'Qǐng dú：Nǐ juéde zhège cài zěnmeyàng?',
    'hsk1_zhe': 'Qǐng dú：Zhè shì shénme?',
    'hsk1_zhongguo': 'Qǐng dú：Wǒ lái zì Zhōngguó.',
    'hsk1_zhongwu': 'Qǐng dú：Zhōngwǔ wǒmen yīqǐ qù chīfàn ba.',
    'hsk1_zhu': 'Qǐng dú：Nǐ zhù zài nǎlǐ?',
    'hsk1_zhuozi': 'Qǐng dú：Shū fàng zài zhuōzi shàng.',
    'hsk1_zi': 'Qǐng dú：Zhège zì zěnme xiě?',
    'hsk1_zuotian': 'Qǐng dú：Zuótiān wǒ jiàn le yīgè lǎo péngyou.',
    'hsk1_zuo2': 'Qǐng dú：Qǐng zuò.',
    'hsk1_zuo': 'Qǐng dú：Wǒ zuò fàn.',
}

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
    {"name": "Wortart"},
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
<div class="german">Wortart: {{Wortart}}</div>
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
<div class="german">Wortart: {{Wortart}}</div>
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
<div class="german">Wortart: {{Wortart}}</div>
""",
    },
]


def validate_deck_structure() -> None:
    """Keep the three task templates and their field contracts in sync."""
    expected_fields = [
        "Hanzi",
        "Pinyin",
        "Meaning",
        "Wortart",
        "AudioSentenceCN",
        "AudioSentenceSound",
        "AudioSentencePY",
        "AudioSentenceDE",
        "ReadingSentenceCN",
        "ReadingSentencePY",
        "ReadingSentenceDE",
    ]
    if [field["name"] for field in FIELDS] != expected_fields:
        raise ValueError("The model must have exactly the eleven expected fields.")

    if [template["name"] for template in TEMPLATES] != [
            "1. Leseverstehen", "2. Hörverstehen", "3. Wortschatz"]:
        raise ValueError("The model must contain reading, listening, and vocabulary templates.")

    reading, listening, vocabulary = TEMPLATES
    reading_front_fields = re.findall(r"{{([^}]+)}}", reading["qfmt"])
    if reading_front_fields != ["ReadingSentenceCN"] or reading["qfmt"].strip() != (
            '<div class="sentence">{{ReadingSentenceCN}}</div>'):
        raise ValueError("The reading-card front must show only its reading sentence.")
    if (
            "{{ReadingSentencePY}}" not in reading["afmt"]
            or "{{Hanzi}}" not in reading["afmt"]
            or "{{Wortart}}" not in reading["afmt"]
            or "Wortart:" not in reading["afmt"]
    ):
        raise ValueError("The reading-card back must reveal its pinyin and focus word.")
    listening_front_fields = re.findall(r"{{([^}]+)}}", listening["qfmt"])
    if listening_front_fields != ["AudioSentenceSound"]:
        raise ValueError("The listening-card front must show only the embedded sound control.")
    if (
            "{{AudioSentenceCN}}" not in listening["afmt"]
            or "{{Hanzi}}" not in listening["afmt"]
            or "{{Wortart}}" not in listening["afmt"]
            or "Wortart:" not in listening["afmt"]
    ):
        raise ValueError("The listening-card back must reveal the sentence and focus word.")
    vocabulary_front_fields = re.findall(r"{{([^}]+)}}", vocabulary["qfmt"])
    if vocabulary_front_fields != ["Hanzi"]:
        raise ValueError("The vocabulary-card front must show only the isolated word.")
    if (
            "{{Pinyin}}" not in vocabulary["afmt"]
            or "{{Meaning}}" not in vocabulary["afmt"]
            or "{{Wortart}}" not in vocabulary["afmt"]
            or "Wortart:" not in vocabulary["afmt"]
    ):
        raise ValueError("The vocabulary-card back must reveal pinyin and meaning.")


def validate_vocabulary() -> None:
    """Fail early if this self-contained source no longer describes HSK 1.0."""
    if len(OFFICIAL_HSK1_WORDS) != 150 or len(HSK1_VOCAB) != 150:
        raise ValueError("HSK 1.0 must contain exactly 150 vocabulary entries.")

    words = [entry[1] for entry in HSK1_VOCAB]
    ids = [entry[0] for entry in HSK1_VOCAB]
    if tuple(words) != OFFICIAL_HSK1_WORDS:
        raise ValueError("HSK1_VOCAB does not match the official HSK 1.0 order.")
    if tuple(OFFICIAL_HSK1_POS) != OFFICIAL_HSK1_WORDS:
        raise ValueError("OFFICIAL_HSK1_POS must cover the official HSK 1.0 words in order.")
    if len(set(words)) != 150 or len(set(ids)) != 150:
        raise ValueError("Vocabulary words and stable IDs must be unique.")
    if set(AUDIO_SENTENCE_PINYIN) != set(ids):
        raise ValueError("Every HSK 1 entry must have one hard-coded audio-sentence pinyin value.")
    if set(READING_SENTENCE_PINYIN) != set(ids):
        raise ValueError("Every HSK 1 entry must have one hard-coded reading-sentence pinyin value.")

    for entry in HSK1_VOCAB:
        if len(entry) != 11 or not entry[0].startswith("hsk1_"):
            raise ValueError(f"Invalid vocabulary entry: {entry!r}")
        (_, word, pinyin, german, audio_zh, audio_py, audio_de, reading_zh,
         reading_py, reading_de, filename) = entry
        if not OFFICIAL_HSK1_POS.get(word, "").strip():
            raise ValueError(f"Missing part-of-speech value for {entry[0]!r}.")
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
         reading_py, reading_de, filename) in HSK1_VOCAB:
        audio_path = AUDIO_DIR / filename
        if not audio_path.is_file():
            raise FileNotFoundError(f"Required listening audio is missing: {audio_path}")
        media_files.append(str(audio_path))
        pos = OFFICIAL_HSK1_POS[chinese]

        deck.add_note(genanki.Note(
            model=model,
            guid=genanki.guid_for("hsk1-german-standalone", vocab_id),
            fields=[
                chinese, pinyin, german, pos, audio_zh, f"[sound:{filename}]", audio_py, audio_de,
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
