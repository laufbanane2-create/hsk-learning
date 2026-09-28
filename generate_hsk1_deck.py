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
DECK_NAME = "HSK 1"
OUTPUT_FILE = "HSK1_DualTask_Deck.apkg"
SCRIPT_DIR = Path(__file__).resolve().parent
AUDIO_DIR = SCRIPT_DIR / "audio"
PINYIN_VALUE_PATTERN = re.compile(r"^[A-Za-zÀ-ɏ ，。！？、：,.!?'']+$")

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

HSK1_VOCAB = [
    ('hsk1_ai', '爱', 'ài', 'lieben', '我爱我的家人。', 'Ich liebe meine Familie.', '爸爸爱妈妈。', 'Papa liebt Mama.', 'hsk1_ai.mp3'),
    ('hsk1_ba2', '八', 'bā', 'acht', '我有八本书。', 'Ich habe acht Bücher.', '我有八个杯子。', 'Ich habe acht Becher.', 'hsk1_ba2.mp3'),
    ('hsk1_ba', '爸爸', 'bàba', 'Papa / Vater', '我爸爸在家工作。', 'Mein Papa arbeitet zu Hause.', '爸爸今天很高兴。', 'Papa ist heute sehr froh.', 'hsk1_ba.mp3'),
    ('hsk1_beizi', '杯子', 'bēizi', 'Tasse / Becher', '我想买一个杯子。', 'Ich möchte einen Becher kaufen.', '杯子里有水。', 'Im Becher ist Wasser.', 'hsk1_beizi.mp3'),
    ('hsk1_beijing', '北京', 'Běijīng', 'Peking', '我住在北京。', 'Ich wohne in Peking.', '我明天去北京。', 'Morgen fahre ich nach Peking.', 'hsk1_beijing.mp3'),
    ('hsk1_ben', '本', 'běn', 'Zählwort für Bücher', '我买了三本书。', 'Ich habe drei Bücher gekauft.', '我买一本书。', 'Ich kaufe ein Buch.', 'hsk1_ben.mp3'),
    ('hsk1_bukeqi', '不客气', 'bù kèqi', 'gern geschehen', '不客气，请坐。', 'Gern geschehen, bitte setz dich.', '我说谢谢，他说不客气。', 'Ich sage danke, er sagt „gern geschehen“.', 'hsk1_bukeqi.mp3'),
    ('hsk1_bu', '不', 'bù', 'nicht / nein', '我不喝水，我喝茶。', 'Ich trinke kein Wasser, ich trinke Tee.', '他不是老师。', 'Er ist kein Lehrer.', 'hsk1_bu.mp3'),
    ('hsk1_cai', '菜', 'cài', 'Gericht / Gemüse', '我喜欢吃中国菜。', 'Ich esse gern chinesisches Essen.', '妈妈做菜。', 'Mama kocht.', 'hsk1_cai.mp3'),
    ('hsk1_cha', '茶', 'chá', 'Tee', '我喜欢喝茶。', 'Ich trinke gern Tee.', '爸爸喝茶。', 'Papa trinkt Tee.', 'hsk1_cha.mp3'),
    ('hsk1_chi', '吃', 'chī', 'essen', '我想吃苹果。', 'Ich möchte einen Apfel essen.', '我们去饭店吃饭。', 'Wir gehen ins Restaurant essen.', 'hsk1_chi.mp3'),
    ('hsk1_chuzuche', '出租车', 'chūzūchē', 'Taxi', '我坐出租车去医院。', 'Ich fahre mit dem Taxi ins Krankenhaus.', '出租车在饭店前面。', 'Das Taxi steht vor dem Restaurant.', 'hsk1_chuzuche.mp3'),
    ('hsk1_dadianhua', '打电话', 'dǎ diànhuà', 'telefonieren / anrufen', '妈妈在打电话。', 'Mama telefoniert gerade.', '我现在打电话。', 'Ich telefoniere jetzt.', 'hsk1_dadianhua.mp3'),
    ('hsk1_da', '大', 'dà', 'groß', '这个苹果很大。', 'Dieser Apfel ist sehr groß.', '我家不大。', 'Mein Zuhause ist nicht groß.', 'hsk1_da.mp3'),
    ('hsk1_de', '的', 'de', 'Possessiv-/Attributpartikel', '这是我的书。', 'Das ist mein Buch.', '这是老师的书。', 'Das ist das Buch des Lehrers.', 'hsk1_de.mp3'),
    ('hsk1_dian', '点', 'diǎn', 'Uhr / Punkt / ein wenig', '现在是三点。', 'Es ist jetzt drei Uhr.', '我们九点去。', 'Wir gehen um neun Uhr.', 'hsk1_dian.mp3'),
    ('hsk1_diannao', '电脑', 'diànnǎo', 'Computer', '他的电脑很漂亮。', 'Sein Computer ist sehr schön.', '电脑在桌子上。', 'Der Computer steht auf dem Tisch.', 'hsk1_diannao.mp3'),
    ('hsk1_dianshi', '电视', 'diànshì', 'Fernseher / Fernsehen', '我喜欢看电视。', 'Ich sehe gern fern.', '爸爸看电视。', 'Papa sieht fern.', 'hsk1_dianshi.mp3'),
    ('hsk1_dianying', '电影', 'diànyǐng', 'Film / Kino', '我们下午去看电影。', 'Wir gehen am Nachmittag ins Kino.', '我明天看电影。', 'Ich sehe morgen einen Film.', 'hsk1_dianying.mp3'),
    ('hsk1_dongxi', '东西', 'dōngxi', 'Sache / Dinge', '你买了什么东西？', 'Was hast du gekauft?', '桌子上有很多东西。', 'Auf dem Tisch sind viele Sachen.', 'hsk1_dongxi.mp3'),
    ('hsk1_dou', '都', 'dōu', 'alle / beide', '我们都是学生。', 'Wir sind alle Schüler.', '我和他都是学生。', 'Er und ich sind beide Schüler.', 'hsk1_dou.mp3'),
    ('hsk1_du', '读', 'dú', 'lesen', '我读书。', 'Ich lese.', '老师读书。', 'Der Lehrer liest.', 'hsk1_du.mp3'),
    ('hsk1_duibuqi', '对不起', 'duìbuqǐ', 'Entschuldigung / es tut mir leid', '对不起，我不认识他。', 'Entschuldigung, ich kenne ihn nicht.', '对不起，我不去。', 'Entschuldigung, ich gehe nicht.', 'hsk1_duibuqi.mp3'),
    ('hsk1_duo', '多', 'duō', 'viel / viele', '这里有很多人。', 'Hier sind viele Leute.', '我有很多书。', 'Ich habe viele Bücher.', 'hsk1_duo.mp3'),
    ('hsk1_duoshao', '多少', 'duōshao', 'wie viel / wie viele', '这个多少钱？', 'Wie viel kostet das?', '你有多少本书？', 'Wie viele Bücher hast du?', 'hsk1_duoshao.mp3'),
    ('hsk1_erzi', '儿子', 'érzi', 'Sohn', '我儿子六岁了。', 'Mein Sohn ist sechs Jahre alt.', '他儿子会写字。', 'Sein Sohn kann schreiben.', 'hsk1_erzi.mp3'),
    ('hsk1_er', '二', 'èr', 'zwei', '我女儿二十岁。', 'Meine Tochter ist zwanzig Jahre alt.', '我有二十块。', 'Ich habe zwanzig Yuan.', 'hsk1_er.mp3'),
    ('hsk1_fandian', '饭店', 'fàndiàn', 'Restaurant', '这家饭店很好。', 'Dieses Restaurant ist sehr gut.', '我们在饭店吃米饭。', 'Wir essen im Restaurant Reis.', 'hsk1_fandian.mp3'),
    ('hsk1_feiji', '飞机', 'fēijī', 'Flugzeug', '我坐飞机去北京。', 'Ich fliege nach Peking.', '爸爸坐飞机。', 'Papa fliegt.', 'hsk1_feiji.mp3'),
    ('hsk1_fenzhong', '分钟', 'fēnzhōng', 'Minute', '我看了五分钟电视。', 'Ich habe fünf Minuten ferngesehen.', '我学习十分钟。', 'Ich lerne zehn Minuten lang.', 'hsk1_fenzhong.mp3'),
    ('hsk1_gaoxing', '高兴', 'gāoxìng', 'froh / glücklich', '认识你我很高兴。', 'Ich freue mich, dich kennenzulernen.', '我今天很高兴。', 'Ich bin heute sehr froh.', 'hsk1_gaoxing.mp3'),
    ('hsk1_ge', '个', 'gè', 'allgemeines Zählwort', '这个人是我的老师。', 'Diese Person ist mein Lehrer.', '我有三个朋友。', 'Ich habe drei Freunde.', 'hsk1_ge.mp3'),
    ('hsk1_gongzuo', '工作', 'gōngzuò', 'arbeiten / Arbeit', '他在医院工作。', 'Er arbeitet im Krankenhaus.', '我爸爸在北京工作。', 'Mein Papa arbeitet in Peking.', 'hsk1_gongzuo.mp3'),
    ('hsk1_gou', '狗', 'gǒu', 'Hund', '我喜欢狗。', 'Ich mag Hunde.', '狗在家里。', 'Der Hund ist zu Hause.', 'hsk1_gou.mp3'),
    ('hsk1_hanyu', '汉语', 'Hànyǔ', 'Chinesisch', '我在学习汉语。', 'Ich lerne Chinesisch.', '我会说汉语。', 'Ich kann Chinesisch sprechen.', 'hsk1_hanyu.mp3'),
    ('hsk1_hao', '好', 'hǎo', 'gut', '今天天气很好。', 'Das Wetter ist heute sehr schön.', '这个老师很好。', 'Dieser Lehrer ist gut.', 'hsk1_hao.mp3'),
    ('hsk1_hao2', '号', 'hào', 'Datum / Nummer', '今天几号？', 'Den Wievielten haben wir heute?', '明天是几号？', 'Welches Datum ist morgen?', 'hsk1_hao2.mp3'),
    ('hsk1_he', '喝', 'hē', 'trinken', '我想喝一杯茶。', 'Ich möchte eine Tasse Tee trinken.', '你喝茶吗？', 'Trinkst du Tee?', 'hsk1_he.mp3'),
    ('hsk1_he2', '和', 'hé', 'und / mit', '我和你是朋友。', 'Du und ich sind Freunde.', '爸爸和妈妈都在家。', 'Papa und Mama sind beide zu Hause.', 'hsk1_he2.mp3'),
    ('hsk1_hen', '很', 'hěn', 'sehr', '这本书很好。', 'Dieses Buch ist sehr gut.', '北京很热吗？', 'Ist es in Peking sehr heiß?', 'hsk1_hen.mp3'),
    ('hsk1_houmian', '后面', 'hòumiàn', 'hinten / hinter', '他在我后面。', 'Er ist hinter mir.', '学校后面有商店。', 'Hinter der Schule gibt es einen Laden.', 'hsk1_houmian.mp3'),
    ('hsk1_hui2', '回', 'huí', 'zurückkehren', '我下午回家。', 'Ich gehe am Nachmittag wieder nach Hause.', '你几点回家？', 'Um wie viel Uhr gehst du nach Hause zurück?', 'hsk1_hui2.mp3'),
    ('hsk1_hui', '会', 'huì', 'können / wissen, wie man', '我会说一点汉语。', 'Ich kann ein bisschen Chinesisch sprechen.', '她会写字。', 'Sie kann schreiben.', 'hsk1_hui.mp3'),
    ('hsk1_ji', '几', 'jǐ', 'wie viele / einige', '你有几个朋友？', 'Wie viele Freunde hast du?', '你有几个杯子？', 'Wie viele Becher hast du?', 'hsk1_ji.mp3'),
    ('hsk1_jia', '家', 'jiā', 'Zuhause / Familie', '我家在北京。', 'Mein Zuhause ist in Peking.', '我家有很多书。', 'Bei mir zu Hause gibt es viele Bücher.', 'hsk1_jia.mp3'),
    ('hsk1_jiao', '叫', 'jiào', 'heißen / nennen', '我叫小明。', 'Ich heiße Xiao Ming.', '他叫什么名字？', 'Wie heißt er?', 'hsk1_jiao.mp3'),
    ('hsk1_jintian', '今天', 'jīntiān', 'heute', '今天是星期几？', 'Welcher Wochentag ist heute?', '今天我们都在家。', 'Heute sind wir alle zu Hause.', 'hsk1_jintian.mp3'),
    ('hsk1_jiu', '九', 'jiǔ', 'neun', '现在九点了。', 'Es ist jetzt neun Uhr.', '他九岁了。', 'Er ist neun Jahre alt.', 'hsk1_jiu.mp3'),
    ('hsk1_kai', '开', 'kāi', 'öffnen / anfangen', '请你开电视。', 'Bitte schalte den Fernseher ein.', '请开电脑。', 'Bitte mach den Computer an.', 'hsk1_kai.mp3'),
    ('hsk1_kan', '看', 'kàn', 'schauen / ansehen / lesen', '我喜欢看书。', 'Ich lese gern.', '我看你的书。', 'Ich lese dein Buch.', 'hsk1_kan.mp3'),
    ('hsk1_kanjian', '看见', 'kànjiàn', 'sehen', '我看见他了。', 'Ich habe ihn gesehen.', '我看见老师了。', 'Ich habe den Lehrer gesehen.', 'hsk1_kanjian.mp3'),
    ('hsk1_kuai', '块', 'kuài', 'Yuan / Stück', '这个苹果一块钱。', 'Dieser Apfel kostet einen Yuan.', '这本书十块。', 'Dieses Buch kostet zehn Yuan.', 'hsk1_kuai.mp3'),
    ('hsk1_lai', '来', 'lái', 'kommen', '请你来我家吃饭。', 'Bitte komm zu mir nach Hause zum Essen.', '明天你来我家吗？', 'Kommst du morgen zu mir nach Hause?', 'hsk1_lai.mp3'),
    ('hsk1_laoshi', '老师', 'lǎoshī', 'Lehrer / Lehrerin', '我的老师很好。', 'Mein Lehrer ist sehr gut.', '老师在学校吗？', 'Ist der Lehrer in der Schule?', 'hsk1_laoshi.mp3'),
    ('hsk1_le', '了', 'le', 'Partikel für abgeschlossene Handlung / Veränderung', '他回家了。', 'Er ist nach Hause gegangen.', '下雨了。', 'Es hat angefangen zu regnen.', 'hsk1_le.mp3'),
    ('hsk1_leng', '冷', 'lěng', 'kalt', '今天很冷。', 'Heute ist es sehr kalt.', '今天不太冷。', 'Heute ist es nicht zu kalt.', 'hsk1_leng.mp3'),
    ('hsk1_li', '里', 'lǐ', 'in / innen', '商店里有很多人。', 'Im Laden sind viele Leute.', '饭店里有米饭。', 'Im Restaurant gibt es Reis.', 'hsk1_li.mp3'),
    ('hsk1_liu', '六', 'liù', 'sechs', '现在是六点。', 'Es ist jetzt sechs Uhr.', '我有六本书。', 'Ich habe sechs Bücher.', 'hsk1_liu.mp3'),
    ('hsk1_mama', '妈妈', 'māma', 'Mama / Mutter', '我妈妈在家做饭。', 'Meine Mama kocht zu Hause.', '妈妈在学校工作。', 'Mama arbeitet in der Schule.', 'hsk1_mama.mp3'),
    ('hsk1_ma', '吗', 'ma', 'Fragepartikel', '你喜欢吃苹果吗？', 'Isst du gern Äpfel?', '你妈妈在家吗？', 'Ist deine Mama zu Hause?', 'hsk1_ma.mp3'),
    ('hsk1_mai', '买', 'mǎi', 'kaufen', '我买了一本书。', 'Ich habe ein Buch gekauft.', '我想买茶。', 'Ich möchte Tee kaufen.', 'hsk1_mai.mp3'),
    ('hsk1_mao', '猫', 'māo', 'Katze', '我很喜欢猫。', 'Ich mag Katzen sehr.', '猫在椅子下面。', 'Die Katze ist unter dem Stuhl.', 'hsk1_mao.mp3'),
    ('hsk1_meiguanxi', '没关系', 'méi guānxi', 'macht nichts / kein Problem', '没关系，我不冷。', 'Macht nichts, mir ist nicht kalt.', '没关系，我们明天去。', 'Kein Problem, wir gehen morgen.', 'hsk1_meiguanxi.mp3'),
    ('hsk1_meiyou', '没有', 'méiyǒu', 'nicht haben / es gibt nicht', '我今天没有钱。', 'Ich habe heute kein Geld.', '我没有电脑。', 'Ich habe keinen Computer.', 'hsk1_meiyou.mp3'),
    ('hsk1_mifan', '米饭', 'mǐfàn', 'gekochter Reis', '我喜欢吃米饭。', 'Ich esse gern Reis.', '我中午吃米饭。', 'Ich esse mittags Reis.', 'hsk1_mifan.mp3'),
    ('hsk1_mingtian', '明天', 'míngtiān', 'morgen', '明天我去学校。', 'Morgen gehe ich zur Schule.', '明天我回北京。', 'Morgen fahre ich zurück nach Peking.', 'hsk1_mingtian.mp3'),
    ('hsk1_mingzi', '名字', 'míngzi', 'Name', '你的名字叫什么？', 'Wie heißt du?', '你的名字怎么写？', 'Wie schreibt man deinen Namen?', 'hsk1_mingzi.mp3'),
    ('hsk1_na', '哪', 'nǎ', 'welche / welcher / welches', '你喜欢哪个杯子？', 'Welchen Becher magst du?', '你想去哪家饭店？', 'In welches Restaurant möchtest du gehen?', 'hsk1_na.mp3'),
    ('hsk1_nar', '哪儿', 'nǎr', 'wo', '你想去哪儿？', 'Wohin möchtest du gehen?', '你的书在哪儿？', 'Wo ist dein Buch?', 'hsk1_nar.mp3'),
    ('hsk1_na2', '那', 'nà', 'das / jenes', '那是我的书。', 'Das ist mein Buch.', '那个是你的杯子吗？', 'Ist jener Becher deiner?', 'hsk1_na2.mp3'),
    ('hsk1_ne', '呢', 'ne', 'Fragepartikel / und?', '我很好，你呢？', "Mir geht's gut, und dir?", '我去北京，你呢？', 'Ich fahre nach Peking, und du?', 'hsk1_ne.mp3'),
    ('hsk1_neng', '能', 'néng', 'können / imstande sein', '我能来。', 'Ich kann kommen.', '明天我不能来。', 'Morgen kann ich nicht kommen.', 'hsk1_neng.mp3'),
    ('hsk1_ni', '你', 'nǐ', 'du / dich', '你好！你叫什么名字？', 'Hallo! Wie heißt du?', '你今天高兴吗？', 'Bist du heute froh?', 'hsk1_ni.mp3'),
    ('hsk1_nian', '年', 'nián', 'Jahr', '今年我二十岁。', 'Dieses Jahr bin ich zwanzig Jahre alt.', '我在中国住了三年。', 'Ich habe drei Jahre in China gewohnt.', 'hsk1_nian.mp3'),
    ('hsk1_nuer', '女儿', "nǚ'ér", 'Tochter', '他女儿很漂亮。', 'Seine Tochter ist sehr hübsch.', '我女儿喜欢看书。', 'Meine Tochter liest gern.', 'hsk1_nuer.mp3'),
    ('hsk1_pengyou', '朋友', 'péngyou', 'Freund / Freundin', '他是我的好朋友。', 'Er ist mein guter Freund.', '他的朋友很多。', 'Er hat viele Freunde.', 'hsk1_pengyou.mp3'),
    ('hsk1_piaoliang', '漂亮', 'piàoliang', 'schön / hübsch', '这个杯子很漂亮。', 'Dieser Becher ist sehr schön.', '她很漂亮。', 'Sie ist sehr hübsch.', 'hsk1_piaoliang.mp3'),
    ('hsk1_pingguo', '苹果', 'píngguǒ', 'Apfel', '桌子上有三个苹果。', 'Auf dem Tisch liegen drei Äpfel.', '我想买苹果。', 'Ich möchte Äpfel kaufen.', 'hsk1_pingguo.mp3'),
    ('hsk1_qi', '七', 'qī', 'sieben', '一个星期有七天。', 'Eine Woche hat sieben Tage.', '我七点回家。', 'Ich gehe um sieben Uhr nach Hause.', 'hsk1_qi.mp3'),
    ('hsk1_qian', '钱', 'qián', 'Geld', '你有多少钱？', 'Wie viel Geld hast du?', '这本书多少钱？', 'Wie viel kostet dieses Buch?', 'hsk1_qian.mp3'),
    ('hsk1_qianmian', '前面', 'qiánmiàn', 'vorne / vor', '学校在前面。', 'Die Schule ist da vorne.', '医院在学校前面。', 'Das Krankenhaus ist vor der Schule.', 'hsk1_qianmian.mp3'),
    ('hsk1_qing', '请', 'qǐng', 'bitte / einladen', '请坐！', 'Bitte setz dich!', '请你看这个字。', 'Bitte schau dir dieses Schriftzeichen an.', 'hsk1_qing.mp3'),
    ('hsk1_qu', '去', 'qù', 'gehen / fahren', '我明天去医院。', 'Ich gehe morgen ins Krankenhaus.', '今天我不去学校。', 'Heute gehe ich nicht zur Schule.', 'hsk1_qu.mp3'),
    ('hsk1_re', '热', 'rè', 'heiß', '今天天气很热。', 'Das Wetter ist heute sehr heiß.', '水很热。', 'Das Wasser ist heiß.', 'hsk1_re.mp3'),
    ('hsk1_ren', '人', 'rén', 'Mensch / Leute', '他是北京人。', 'Er kommt aus Peking.', '那个人是我爸爸。', 'Diese Person ist mein Papa.', 'hsk1_ren.mp3'),
    ('hsk1_renshi', '认识', 'rènshi', 'kennen / erkennen', '我认识他。', 'Ich kenne ihn.', '你认识他吗？', 'Kennst du ihn?', 'hsk1_renshi.mp3'),
    ('hsk1_san', '三', 'sān', 'drei', '我有三个女儿。', 'Ich habe drei Töchter.', '桌子上有三个杯子。', 'Auf dem Tisch stehen drei Becher.', 'hsk1_san.mp3'),
    ('hsk1_shangdian', '商店', 'shāngdiàn', 'Geschäft / Laden', '我去商店买水果。', 'Ich gehe in den Laden, um Obst zu kaufen.', '商店里有水果吗？', 'Gibt es im Laden Obst?', 'hsk1_shangdian.mp3'),
    ('hsk1_shang', '上', 'shàng', 'auf / oben', '书在桌子上。', 'Das Buch liegt auf dem Tisch.', '杯子在桌子上。', 'Der Becher steht auf dem Tisch.', 'hsk1_shang.mp3'),
    ('hsk1_shangwu', '上午', 'shàngwǔ', 'Vormittag', '上午我在家工作。', 'Am Vormittag arbeite ich zu Hause.', '我上午去学校。', 'Ich gehe vormittags zur Schule.', 'hsk1_shangwu.mp3'),
    ('hsk1_shao', '少', 'shǎo', 'wenig / wenige', '这里人很少。', 'Hier sind nur wenige Leute.', '我们学校人很少。', 'An unserer Schule sind nur wenige Leute.', 'hsk1_shao.mp3'),
    ('hsk1_shei', '谁', 'shéi', 'wer', '那个人是谁？', 'Wer ist diese Person?', '谁是你的老师？', 'Wer ist dein Lehrer?', 'hsk1_shei.mp3'),
    ('hsk1_shenme', '什么', 'shénme', 'was', '你想吃什么？', 'Was möchtest du essen?', '你在写什么？', 'Was schreibst du?', 'hsk1_shenme.mp3'),
    ('hsk1_shi2', '十', 'shí', 'zehn', '我有十个苹果。', 'Ich habe zehn Äpfel.', '十点我们去饭店。', 'Um zehn Uhr gehen wir ins Restaurant.', 'hsk1_shi2.mp3'),
    ('hsk1_shihou', '时候', 'shíhou', 'Zeitpunkt / Zeit', '你什么时候来我家？', 'Wann kommst du zu mir nach Hause?', '我小的时候住在北京。', 'Als ich klein war, habe ich in Peking gewohnt.', 'hsk1_shihou.mp3'),
    ('hsk1_shi', '是', 'shì', 'sein', '我是学生。', 'Ich bin Schüler.', '这是我妈妈。', 'Das ist meine Mama.', 'hsk1_shi.mp3'),
    ('hsk1_shu', '书', 'shū', 'Buch', '这本书是我的。', 'Dieses Buch gehört mir.', '你的书在桌子上。', 'Dein Buch liegt auf dem Tisch.', 'hsk1_shu.mp3'),
    ('hsk1_shui', '水', 'shuǐ', 'Wasser', '我喝了很多水。', 'Ich habe viel Wasser getrunken.', '我想喝水。', 'Ich möchte Wasser trinken.', 'hsk1_shui.mp3'),
    ('hsk1_shuiguo', '水果', 'shuǐguǒ', 'Obst', '我喜欢吃水果。', 'Ich esse gern Obst.', '我买了一些水果。', 'Ich habe etwas Obst gekauft.', 'hsk1_shuiguo.mp3'),
    ('hsk1_shuijiao', '睡觉', 'shuìjiào', 'schlafen', '我十一点睡觉。', 'Ich gehe um elf Uhr schlafen.', '他十点睡觉。', 'Er geht um zehn Uhr schlafen.', 'hsk1_shuijiao.mp3'),
    ('hsk1_shuo', '说', 'shuō', 'sprechen / sagen', '他说他明天来。', 'Er sagt, dass er morgen kommt.', '你会说汉语吗？', 'Kannst du Chinesisch sprechen?', 'hsk1_shuo.mp3'),
    ('hsk1_si', '四', 'sì', 'vier', '我买了四本书。', 'Ich habe vier Bücher gekauft.', '四点我回家。', 'Um vier Uhr gehe ich nach Hause.', 'hsk1_si.mp3'),
    ('hsk1_sui', '岁', 'suì', 'Jahre alt', '他今年二十五岁了。', 'Er ist dieses Jahr fünfundzwanzig Jahre alt.', '我妈妈四十岁。', 'Meine Mama ist vierzig Jahre alt.', 'hsk1_sui.mp3'),
    ('hsk1_ta', '他', 'tā', 'er / ihn', '他是我的老师。', 'Er ist mein Lehrer.', '他是我的朋友。', 'Er ist mein Freund.', 'hsk1_ta.mp3'),
    ('hsk1_ta2', '她', 'tā', 'sie / ihr', '她是我的好朋友。', 'Sie ist meine gute Freundin.', '她喜欢喝茶。', 'Sie trinkt gern Tee.', 'hsk1_ta2.mp3'),
    ('hsk1_tai', '太', 'tài', 'zu / allzu', '今天太热了。', 'Heute ist es zu heiß.', '我的桌子太小了。', 'Mein Tisch ist zu klein.', 'hsk1_tai.mp3'),
    ('hsk1_tianqi', '天气', 'tiānqì', 'Wetter', '今天天气怎么样？', 'Wie ist das Wetter heute?', '北京天气怎么样？', 'Wie ist das Wetter in Peking?', 'hsk1_tianqi.mp3'),
    ('hsk1_ting', '听', 'tīng', 'hören', '请听我说。', 'Bitte hör mir zu.', '我喜欢听汉语。', 'Ich höre gern Chinesisch.', 'hsk1_ting.mp3'),
    ('hsk1_tongxue', '同学', 'tóngxué', 'Mitschüler / Mitschülerin', '他是我的同学。', 'Er ist mein Mitschüler.', '我的同学都在北京。', 'Meine Mitschüler sind alle in Peking.', 'hsk1_tongxue.mp3'),
    ('hsk1_wei', '喂', 'wèi', 'hallo (am Telefon)', '喂，李老师在吗？', 'Hallo, ist Lehrer Li da?', '喂，你在家吗？', 'Hallo, bist du zu Hause?', 'hsk1_wei.mp3'),
    ('hsk1_wo', '我', 'wǒ', 'ich / mich', '我是中国人。', 'Ich bin Chinese.', '我不是学生。', 'Ich bin kein Schüler.', 'hsk1_wo.mp3'),
    ('hsk1_women', '我们', 'wǒmen', 'wir / uns', '我们是同学。', 'Wir sind Mitschüler.', '我们都是中国人。', 'Wir sind alle Chinesen.', 'hsk1_women.mp3'),
    ('hsk1_wu', '五', 'wǔ', 'fünf', '我有五本汉语书。', 'Ich habe fünf Chinesischbücher.', '五点我去饭店。', 'Um fünf Uhr gehe ich ins Restaurant.', 'hsk1_wu.mp3'),
    ('hsk1_xihuan', '喜欢', 'xǐhuan', 'mögen', '我喜欢中国。', 'Ich mag China.', '我喜欢这个杯子。', 'Ich mag diesen Becher.', 'hsk1_xihuan.mp3'),
    ('hsk1_xia', '下', 'xià', 'unter / unten', '猫在桌子下面。', 'Die Katze ist unter dem Tisch.', '书在桌子下面。', 'Das Buch ist unter dem Tisch.', 'hsk1_xia.mp3'),
    ('hsk1_xiawu', '下午', 'xiàwǔ', 'Nachmittag', '下午我去商店。', 'Am Nachmittag gehe ich in den Laden.', '下午我想看电影。', 'Am Nachmittag möchte ich einen Film sehen.', 'hsk1_xiawu.mp3'),
    ('hsk1_xiayu', '下雨', 'xià yǔ', 'regnen', '昨天下雨了。', 'Gestern hat es geregnet.', '今天下雨，我们不去学校。', 'Heute regnet es, wir gehen nicht zur Schule.', 'hsk1_xiayu.mp3'),
    ('hsk1_xiansheng', '先生', 'xiānsheng', 'Herr / Ehemann', '王先生，您好！', 'Guten Tag, Herr Wang!', '先生，请坐。', 'Bitte, mein Herr, setzen Sie sich.', 'hsk1_xiansheng.mp3'),
    ('hsk1_xianzai', '现在', 'xiànzài', 'jetzt', '现在几点了？', 'Wie spät ist es jetzt?', '现在我们去饭店。', 'Jetzt gehen wir ins Restaurant.', 'hsk1_xianzai.mp3'),
    ('hsk1_xiang', '想', 'xiǎng', 'wollen / denken / vermissen', '我想回家。', 'Ich möchte nach Hause gehen.', '你想喝水吗？', 'Möchtest du Wasser trinken?', 'hsk1_xiang.mp3'),
    ('hsk1_xiao', '小', 'xiǎo', 'klein', '我家很小。', 'Mein Zuhause ist sehr klein.', '这个杯子很小。', 'Dieser Becher ist sehr klein.', 'hsk1_xiao.mp3'),
    ('hsk1_xiaojie', '小姐', 'xiǎojie', 'junge Dame', '小姐，您叫什么名字？', 'Junge Dame, wie heißen Sie?', '小姐，请坐。', 'Junge Dame, bitte setzen Sie sich.', 'hsk1_xiaojie.mp3'),
    ('hsk1_xie', '些', 'xiē', 'einige / ein paar', '我想喝一些茶。', 'Ich möchte etwas Tee trinken.', '我买了一些书。', 'Ich habe einige Bücher gekauft.', 'hsk1_xie.mp3'),
    ('hsk1_xie2', '写', 'xiě', 'schreiben', '我写汉字。', 'Ich schreibe chinesische Schriftzeichen.', '请写你的名字。', 'Bitte schreib deinen Namen.', 'hsk1_xie2.mp3'),
    ('hsk1_xiexie', '谢谢', 'xièxie', 'danke', '谢谢你，老师！', 'Vielen Dank, Herr Lehrer!', '谢谢你来我家。', 'Danke, dass du zu mir nach Hause kommst.', 'hsk1_xiexie.mp3'),
    ('hsk1_xingqi', '星期', 'xīngqī', 'Woche', '这个星期我不工作。', 'Diese Woche arbeite ich nicht.', '今天星期三。', 'Heute ist Mittwoch.', 'hsk1_xingqi.mp3'),
    ('hsk1_xuesheng', '学生', 'xuésheng', 'Schüler / Schülerin', '他们都是学生。', 'Sie sind alle Schüler.', '他是我的学生。', 'Er ist mein Schüler.', 'hsk1_xuesheng.mp3'),
    ('hsk1_xuexi', '学习', 'xuéxí', 'lernen / studieren', '我喜欢学习汉语。', 'Ich lerne gern Chinesisch.', '他在学校学习汉语。', 'Er lernt in der Schule Chinesisch.', 'hsk1_xuexi.mp3'),
    ('hsk1_xuexiao', '学校', 'xuéxiào', 'Schule', '学校在我家后面。', 'Die Schule ist hinter meinem Haus.', '学校里有很多学生。', 'In der Schule gibt es viele Schüler.', 'hsk1_xuexiao.mp3'),
    ('hsk1_yi', '一', 'yī', 'eins', '我有一个女儿。', 'Ich habe eine Tochter.', '我有一个朋友。', 'Ich habe einen Freund.', 'hsk1_yi.mp3'),
    ('hsk1_yidianr', '一点儿', 'yīdiǎnr', 'ein bisschen', '我会说一点儿汉语。', 'Ich kann ein bisschen Chinesisch sprechen.', '我想喝一点儿水。', 'Ich möchte ein wenig Wasser trinken.', 'hsk1_yidianr.mp3'),
    ('hsk1_yifu', '衣服', 'yīfu', 'Kleidung', '我买了很多衣服。', 'Ich habe viele Kleidungsstücke gekauft.', '她的衣服很漂亮。', 'Ihre Kleidung ist sehr schön.', 'hsk1_yifu.mp3'),
    ('hsk1_yisheng', '医生', 'yīshēng', 'Arzt / Ärztin', '我妈妈是医生。', 'Meine Mama ist Ärztin.', '医生在医院吗？', 'Ist der Arzt im Krankenhaus?', 'hsk1_yisheng.mp3'),
    ('hsk1_yiyuan', '医院', 'yīyuàn', 'Krankenhaus', '医院在哪儿？', 'Wo ist das Krankenhaus?', '我妈妈在医院。', 'Meine Mama ist im Krankenhaus.', 'hsk1_yiyuan.mp3'),
    ('hsk1_yizi', '椅子', 'yǐzi', 'Stuhl', '椅子在桌子后面。', 'Der Stuhl steht hinter dem Tisch.', '老师坐在椅子上。', 'Der Lehrer sitzt auf dem Stuhl.', 'hsk1_yizi.mp3'),
    ('hsk1_you', '有', 'yǒu', 'haben / es gibt', '你有电脑吗？', 'Hast du einen Computer?', '学校里有很多书。', 'In der Schule gibt es viele Bücher.', 'hsk1_you.mp3'),
    ('hsk1_yue', '月', 'yuè', 'Monat', '一年有十二个月。', 'Ein Jahr hat zwölf Monate.', '二月北京很冷。', 'Im Februar ist es in Peking sehr kalt.', 'hsk1_yue.mp3'),
    ('hsk1_zai', '在', 'zài', 'in / an / sich befinden', '他在哪里工作？', 'Wo arbeitet er?', '我爸爸在北京。', 'Mein Papa ist in Peking.', 'hsk1_zai.mp3'),
    ('hsk1_zaijian', '再见', 'zàijiàn', 'auf Wiedersehen', '老师，再见！', 'Auf Wiedersehen, Herr Lehrer!', '我们今天下午再见。', 'Wir sehen uns heute Nachmittag.', 'hsk1_zaijian.mp3'),
    ('hsk1_zenme', '怎么', 'zěnme', 'wie / warum', '你怎么不去？', 'Warum gehst du nicht?', '你怎么去学校？', 'Wie gehst du zur Schule?', 'hsk1_zenme.mp3'),
    ('hsk1_zenmeyang', '怎么样', 'zěnmeyàng', 'wie / wie wäre es / wie ist', '这个饭店怎么样？', 'Wie ist dieses Restaurant?', '你妈妈怎么样？', 'Wie geht es deiner Mama?', 'hsk1_zenmeyang.mp3'),
    ('hsk1_zhe', '这', 'zhè', 'dies / das hier', '这是什么？', 'Was ist das?', '这是我的电脑。', 'Das ist mein Computer.', 'hsk1_zhe.mp3'),
    ('hsk1_zhongguo', '中国', 'Zhōngguó', 'China', '中国很大。', 'China ist sehr groß.', '他在中国学习汉语。', 'Er lernt in China Chinesisch.', 'hsk1_zhongguo.mp3'),
    ('hsk1_zhongwu', '中午', 'zhōngwǔ', 'Mittag', '中午我在家吃饭。', 'Mittags esse ich zu Hause.', '中午我们去饭店。', 'Mittags gehen wir ins Restaurant.', 'hsk1_zhongwu.mp3'),
    ('hsk1_zhu', '住', 'zhù', 'wohnen', '你住在哪里？', 'Wo wohnst du?', '我住在学校后面。', 'Ich wohne hinter der Schule.', 'hsk1_zhu.mp3'),
    ('hsk1_zhuozi', '桌子', 'zhuōzi', 'Tisch', '我的桌子很大。', 'Mein Tisch ist sehr groß.', '桌子上有一本书。', 'Auf dem Tisch liegt ein Buch.', 'hsk1_zhuozi.mp3'),
    ('hsk1_zi', '字', 'zì', 'Zeichen / Schriftzeichen', '这个字怎么写？', 'Wie schreibt man dieses Zeichen?', '这个字怎么读？', 'Wie liest man dieses Schriftzeichen?', 'hsk1_zi.mp3'),
    ('hsk1_zuotian', '昨天', 'zuótiān', 'gestern', '昨天是星期几？', 'Welcher Wochentag war gestern?', '昨天我们看电影了。', 'Gestern haben wir einen Film gesehen.', 'hsk1_zuotian.mp3'),
    ('hsk1_zuo2', '坐', 'zuò', 'sitzen', '请坐。', 'Bitte setz dich.', '你坐出租车吗？', 'Fährst du mit dem Taxi?', 'hsk1_zuo2.mp3'),
    ('hsk1_zuo', '做', 'zuò', 'machen / tun', '我做饭。', 'Ich koche.', '妈妈在家做米饭。', 'Mama macht zu Hause Reis.', 'hsk1_zuo.mp3'),
]

AUDIO_SENTENCE_PINYIN = {
    'hsk1_ai': 'Wǒ ài wǒ de jiārén.',
    'hsk1_ba2': 'Wǒ yǒu bā běn shū.',
    'hsk1_ba': 'Wǒ bàba zài jiā gōngzuò.',
    'hsk1_beizi': 'Wǒ xiǎng mǎi yī gè bēizi.',
    'hsk1_beijing': 'Wǒ zhù zài Běijīng.',
    'hsk1_ben': 'Wǒ mǎi le sān běn shū.',
    'hsk1_bukeqi': 'Bù kèqi, qǐng zuò.',
    'hsk1_bu': 'Wǒ bù hē shuǐ, wǒ hē chá.',
    'hsk1_cai': 'Wǒ xǐhuan chī Zhōngguó cài.',
    'hsk1_cha': 'Wǒ xǐhuan hē chá.',
    'hsk1_chi': 'Wǒ xiǎng chī píngguǒ.',
    'hsk1_chuzuche': 'Wǒ zuò chūzūchē qù yīyuàn.',
    'hsk1_dadianhua': 'Māma zài dǎ diànhuà.',
    'hsk1_da': 'Zhège píngguǒ hěn dà.',
    'hsk1_de': 'Zhè shì wǒ de shū.',
    'hsk1_dian': 'Xiànzài shì sān diǎn.',
    'hsk1_diannao': 'Tā de diànnǎo hěn piàoliang.',
    'hsk1_dianshi': 'Wǒ xǐhuan kàn diànshì.',
    'hsk1_dianying': 'Wǒmen xiàwǔ qù kàn diànyǐng.',
    'hsk1_dongxi': 'Nǐ mǎi le shénme dōngxi?',
    'hsk1_dou': 'Wǒmen dōu shì xuésheng.',
    'hsk1_du': 'Wǒ dú shū.',
    'hsk1_duibuqi': 'Duìbuqǐ, wǒ bù rènshi tā.',
    'hsk1_duo': 'Zhèlǐ yǒu hěn duō rén.',
    'hsk1_duoshao': 'Zhège duōshao qián?',
    'hsk1_erzi': 'Wǒ érzi liù suì le.',
    'hsk1_er': "Wǒ nǚ'ér èrshí suì.",
    'hsk1_fandian': 'Zhè jiā fàndiàn hěn hǎo.',
    'hsk1_feiji': 'Wǒ zuò fēijī qù Běijīng.',
    'hsk1_fenzhong': 'Wǒ kàn le wǔ fēnzhōng diànshì.',
    'hsk1_gaoxing': 'Rènshi nǐ wǒ hěn gāoxìng.',
    'hsk1_ge': 'Zhège rén shì wǒ de lǎoshī.',
    'hsk1_gongzuo': 'Tā zài yīyuàn gōngzuò.',
    'hsk1_gou': 'Wǒ xǐhuan gǒu.',
    'hsk1_hanyu': 'Wǒ zài xuéxí Hànyǔ.',
    'hsk1_hao': 'Jīntiān tiānqì hěn hǎo.',
    'hsk1_hao2': 'Jīntiān jǐ hào?',
    'hsk1_he': 'Wǒ xiǎng hē yī bēi chá.',
    'hsk1_he2': 'Wǒ hé nǐ shì péngyou.',
    'hsk1_hen': 'Zhè běn shū hěn hǎo.',
    'hsk1_houmian': 'Tā zài wǒ hòumiàn.',
    'hsk1_hui2': 'Wǒ xiàwǔ huí jiā.',
    'hsk1_hui': 'Wǒ huì shuō yīdiǎn Hànyǔ.',
    'hsk1_ji': 'Nǐ yǒu jǐ gè péngyou?',
    'hsk1_jia': 'Wǒ jiā zài Běijīng.',
    'hsk1_jiao': 'Wǒ jiào Xiǎo Míng.',
    'hsk1_jintian': 'Jīntiān shì xīngqī jǐ?',
    'hsk1_jiu': 'Xiànzài jiǔ diǎn le.',
    'hsk1_kai': 'Qǐng nǐ kāi diànshì.',
    'hsk1_kan': 'Wǒ xǐhuan kàn shū.',
    'hsk1_kanjian': 'Wǒ kànjiàn tā le.',
    'hsk1_kuai': 'Zhège píngguǒ yī kuài qián.',
    'hsk1_lai': 'Qǐng nǐ lái wǒ jiā chīfàn.',
    'hsk1_laoshi': 'Wǒ de lǎoshī hěn hǎo.',
    'hsk1_le': 'Tā huí jiā le.',
    'hsk1_leng': 'Jīntiān hěn lěng.',
    'hsk1_li': 'Shāngdiàn lǐ yǒu hěn duō rén.',
    'hsk1_liu': 'Xiànzài shì liù diǎn.',
    'hsk1_mama': 'Wǒ māma zài jiā zuòfàn.',
    'hsk1_ma': 'Nǐ xǐhuan chī píngguǒ ma?',
    'hsk1_mai': 'Wǒ mǎi le yī běn shū.',
    'hsk1_mao': 'Wǒ hěn xǐhuan māo.',
    'hsk1_meiguanxi': 'Méi guānxi, wǒ bù lěng.',
    'hsk1_meiyou': 'Wǒ jīntiān méiyǒu qián.',
    'hsk1_mifan': 'Wǒ xǐhuan chī mǐfàn.',
    'hsk1_mingtian': 'Míngtiān wǒ qù xuéxiào.',
    'hsk1_mingzi': 'Nǐ de míngzi jiào shénme?',
    'hsk1_na': 'Nǐ xǐhuan nǎge bēizi?',
    'hsk1_nar': 'Nǐ xiǎng qù nǎr?',
    'hsk1_na2': 'Nà shì wǒ de shū.',
    'hsk1_ne': 'Wǒ hěn hǎo, nǐ ne?',
    'hsk1_neng': 'Wǒ néng lái.',
    'hsk1_ni': 'Nǐ hǎo! Nǐ jiào shénme míngzi?',
    'hsk1_nian': 'Jīnnián wǒ èrshí suì.',
    'hsk1_nuer': "Tā nǚ'ér hěn piàoliang.",
    'hsk1_pengyou': 'Tā shì wǒ de hǎo péngyou.',
    'hsk1_piaoliang': 'Zhège bēizi hěn piàoliang.',
    'hsk1_pingguo': 'Zhuōzi shàng yǒu sān gè píngguǒ.',
    'hsk1_qi': 'Yī gè xīngqī yǒu qī tiān.',
    'hsk1_qian': 'Nǐ yǒu duōshao qián?',
    'hsk1_qianmian': 'Xuéxiào zài qiánmiàn.',
    'hsk1_qing': 'Qǐng zuò!',
    'hsk1_qu': 'Wǒ míngtiān qù yīyuàn.',
    'hsk1_re': 'Jīntiān tiānqì hěn rè.',
    'hsk1_ren': 'Tā shì Běijīng rén.',
    'hsk1_renshi': 'Wǒ rènshi tā.',
    'hsk1_san': "Wǒ yǒu sān gè nǚ'ér.",
    'hsk1_shangdian': 'Wǒ qù shāngdiàn mǎi shuǐguǒ.',
    'hsk1_shang': 'Shū zài zhuōzi shàng.',
    'hsk1_shangwu': 'Shàngwǔ wǒ zài jiā gōngzuò.',
    'hsk1_shao': 'Zhèlǐ rén hěn shǎo.',
    'hsk1_shei': 'Nàge rén shì shéi?',
    'hsk1_shenme': 'Nǐ xiǎng chī shénme?',
    'hsk1_shi2': 'Wǒ yǒu shí gè píngguǒ.',
    'hsk1_shihou': 'Nǐ shénme shíhou lái wǒ jiā?',
    'hsk1_shi': 'Wǒ shì xuésheng.',
    'hsk1_shu': 'Zhè běn shū shì wǒ de.',
    'hsk1_shui': 'Wǒ hē le hěn duō shuǐ.',
    'hsk1_shuiguo': 'Wǒ xǐhuan chī shuǐguǒ.',
    'hsk1_shuijiao': 'Wǒ shíyī diǎn shuìjiào.',
    'hsk1_shuo': 'Tā shuō tā míngtiān lái.',
    'hsk1_si': 'Wǒ mǎi le sì běn shū.',
    'hsk1_sui': 'Tā jīnnián èrshíwǔ suì le.',
    'hsk1_ta': 'Tā shì wǒ de lǎoshī.',
    'hsk1_ta2': 'Tā shì wǒ de hǎo péngyou.',
    'hsk1_tai': 'Jīntiān tài rè le.',
    'hsk1_tianqi': 'Jīntiān tiānqì zěnmeyàng?',
    'hsk1_ting': 'Qǐng tīng wǒ shuō.',
    'hsk1_tongxue': 'Tā shì wǒ de tóngxué.',
    'hsk1_wei': 'Wèi, Lǐ lǎoshī zài ma?',
    'hsk1_wo': 'Wǒ shì Zhōngguó rén.',
    'hsk1_women': 'Wǒmen shì tóngxué.',
    'hsk1_wu': 'Wǒ yǒu wǔ běn Hànyǔ shū.',
    'hsk1_xihuan': 'Wǒ xǐhuan Zhōngguó.',
    'hsk1_xia': 'Māo zài zhuōzi xiàmiàn.',
    'hsk1_xiawu': 'Xiàwǔ wǒ qù shāngdiàn.',
    'hsk1_xiayu': 'Zuótiān xià yǔ le.',
    'hsk1_xiansheng': 'Wáng xiānsheng, nín hǎo!',
    'hsk1_xianzai': 'Xiànzài jǐ diǎn le?',
    'hsk1_xiang': 'Wǒ xiǎng huí jiā.',
    'hsk1_xiao': 'Wǒ jiā hěn xiǎo.',
    'hsk1_xiaojie': 'Xiǎojie, nín jiào shénme míngzi?',
    'hsk1_xie': 'Wǒ xiǎng hē yīxiē chá.',
    'hsk1_xie2': 'Wǒ xiě Hànzì.',
    'hsk1_xiexie': 'Xièxie nǐ, lǎoshī!',
    'hsk1_xingqi': 'Zhège xīngqī wǒ bù gōngzuò.',
    'hsk1_xuesheng': 'Tāmen dōu shì xuésheng.',
    'hsk1_xuexi': 'Wǒ xǐhuan xuéxí Hànyǔ.',
    'hsk1_xuexiao': 'Xuéxiào zài wǒ jiā hòumiàn.',
    'hsk1_yi': "Wǒ yǒu yī gè nǚ'ér.",
    'hsk1_yidianr': 'Wǒ huì shuō yīdiǎnr Hànyǔ.',
    'hsk1_yifu': 'Wǒ mǎi le hěn duō yīfu.',
    'hsk1_yisheng': 'Wǒ māma shì yīshēng.',
    'hsk1_yiyuan': 'Yīyuàn zài nǎr?',
    'hsk1_yizi': 'Yǐzi zài zhuōzi hòumiàn.',
    'hsk1_you': 'Nǐ yǒu diànnǎo ma?',
    'hsk1_yue': "Yī nián yǒu shí'èr gè yuè.",
    'hsk1_zai': 'Tā zài nǎlǐ gōngzuò?',
    'hsk1_zaijian': 'Lǎoshī, zàijiàn!',
    'hsk1_zenme': 'Nǐ zěnme bù qù?',
    'hsk1_zenmeyang': 'Zhège fàndiàn zěnmeyàng?',
    'hsk1_zhe': 'Zhè shì shénme?',
    'hsk1_zhongguo': 'Zhōngguó hěn dà.',
    'hsk1_zhongwu': 'Zhōngwǔ wǒ zài jiā chīfàn.',
    'hsk1_zhu': 'Nǐ zhù zài nǎlǐ?',
    'hsk1_zhuozi': 'Wǒ de zhuōzi hěn dà.',
    'hsk1_zi': 'Zhège zì zěnme xiě?',
    'hsk1_zuotian': 'Zuótiān shì xīngqī jǐ?',
    'hsk1_zuo2': 'Qǐng zuò.',
    'hsk1_zuo': 'Wǒ zuò fàn.',
}

READING_SENTENCE_PINYIN = {
    'hsk1_ai': 'Bàba ài māma.',
    'hsk1_ba2': 'Wǒ yǒu bā gè bēizi.',
    'hsk1_ba': 'Bàba jīntiān hěn gāoxìng.',
    'hsk1_beizi': 'Bēizi lǐ yǒu shuǐ.',
    'hsk1_beijing': 'Wǒ míngtiān qù Běijīng.',
    'hsk1_ben': 'Wǒ mǎi yī běn shū.',
    'hsk1_bukeqi': 'Wǒ shuō xièxie, tā shuō bù kèqi.',
    'hsk1_bu': 'Tā bù shì lǎoshī.',
    'hsk1_cai': 'Māma zuò cài.',
    'hsk1_cha': 'Bàba hē chá.',
    'hsk1_chi': 'Wǒmen qù fàndiàn chīfàn.',
    'hsk1_chuzuche': 'Chūzūchē zài fàndiàn qiánmiàn.',
    'hsk1_dadianhua': 'Wǒ xiànzài dǎ diànhuà.',
    'hsk1_da': 'Wǒ jiā bù dà.',
    'hsk1_de': 'Zhè shì lǎoshī de shū.',
    'hsk1_dian': 'Wǒmen jiǔ diǎn qù.',
    'hsk1_diannao': 'Diànnǎo zài zhuōzi shàng.',
    'hsk1_dianshi': 'Bàba kàn diànshì.',
    'hsk1_dianying': 'Wǒ míngtiān kàn diànyǐng.',
    'hsk1_dongxi': 'Zhuōzi shàng yǒu hěn duō dōngxi.',
    'hsk1_dou': 'Wǒ hé tā dōu shì xuésheng.',
    'hsk1_du': 'Lǎoshī dú shū.',
    'hsk1_duibuqi': 'Duìbuqǐ, wǒ bù qù.',
    'hsk1_duo': 'Wǒ yǒu hěn duō shū.',
    'hsk1_duoshao': 'Nǐ yǒu duōshao běn shū?',
    'hsk1_erzi': 'Tā érzi huì xiě zì.',
    'hsk1_er': 'Wǒ yǒu èr shí kuài.',
    'hsk1_fandian': 'Wǒmen zài fàndiàn chī mǐfàn.',
    'hsk1_feiji': 'Bàba zuò fēijī.',
    'hsk1_fenzhong': 'Wǒ xuéxí shí fēnzhōng.',
    'hsk1_gaoxing': 'Wǒ jīntiān hěn gāoxìng.',
    'hsk1_ge': 'Wǒ yǒu sān gè péngyou.',
    'hsk1_gongzuo': 'Wǒ bàba zài Běijīng gōngzuò.',
    'hsk1_gou': 'Gǒu zài jiā lǐ.',
    'hsk1_hanyu': 'Wǒ huì shuō Hànyǔ.',
    'hsk1_hao': 'Zhège lǎoshī hěn hǎo.',
    'hsk1_hao2': 'Míngtiān shì jǐ hào?',
    'hsk1_he': 'Nǐ hē chá ma?',
    'hsk1_he2': 'Bàba hé māma dōu zài jiā.',
    'hsk1_hen': 'Běijīng hěn rè ma?',
    'hsk1_houmian': 'Xuéxiào hòumiàn yǒu shāngdiàn.',
    'hsk1_hui2': 'Nǐ jǐ diǎn huí jiā?',
    'hsk1_hui': 'Tā huì xiě zì.',
    'hsk1_ji': 'Nǐ yǒu jǐ gè bēizi?',
    'hsk1_jia': 'Wǒ jiā yǒu hěn duō shū.',
    'hsk1_jiao': 'Tā jiào shénme míngzi?',
    'hsk1_jintian': 'Jīntiān wǒmen dōu zài jiā.',
    'hsk1_jiu': 'Tā jiǔ suì le.',
    'hsk1_kai': 'Qǐng kāi diànnǎo.',
    'hsk1_kan': 'Wǒ kàn nǐ de shū.',
    'hsk1_kanjian': 'Wǒ kànjiàn lǎoshī le.',
    'hsk1_kuai': 'Zhè běn shū shí kuài.',
    'hsk1_lai': 'Míngtiān nǐ lái wǒ jiā ma?',
    'hsk1_laoshi': 'Lǎoshī zài xuéxiào ma?',
    'hsk1_le': 'Xià yǔ le.',
    'hsk1_leng': 'Jīntiān bù tài lěng.',
    'hsk1_li': 'Fàndiàn lǐ yǒu mǐfàn.',
    'hsk1_liu': 'Wǒ yǒu liù běn shū.',
    'hsk1_mama': 'Māma zài xuéxiào gōngzuò.',
    'hsk1_ma': 'Nǐ māma zài jiā ma?',
    'hsk1_mai': 'Wǒ xiǎng mǎi chá.',
    'hsk1_mao': 'Māo zài yǐzi xiàmiàn.',
    'hsk1_meiguanxi': 'Méi guānxi, wǒmen míngtiān qù.',
    'hsk1_meiyou': 'Wǒ méiyǒu diànnǎo.',
    'hsk1_mifan': 'Wǒ zhōngwǔ chī mǐfàn.',
    'hsk1_mingtian': 'Míngtiān wǒ huí Běijīng.',
    'hsk1_mingzi': 'Nǐ de míngzi zěnme xiě?',
    'hsk1_na': 'Nǐ xiǎng qù nǎ jiā fàndiàn?',
    'hsk1_nar': 'Nǐ de shū zài nǎr?',
    'hsk1_na2': 'Nàge shì nǐ de bēizi ma?',
    'hsk1_ne': 'Wǒ qù Běijīng, nǐ ne?',
    'hsk1_neng': 'Míngtiān wǒ bù néng lái.',
    'hsk1_ni': 'Nǐ jīntiān gāoxìng ma?',
    'hsk1_nian': 'Wǒ zài Zhōngguó zhù le sān nián.',
    'hsk1_nuer': "Wǒ nǚ'ér xǐhuan kàn shū.",
    'hsk1_pengyou': 'Tā de péngyou hěn duō.',
    'hsk1_piaoliang': 'Tā hěn piàoliang.',
    'hsk1_pingguo': 'Wǒ xiǎng mǎi píngguǒ.',
    'hsk1_qi': 'Wǒ qī diǎn huí jiā.',
    'hsk1_qian': 'Zhè běn shū duōshao qián?',
    'hsk1_qianmian': 'Yīyuàn zài xuéxiào qiánmiàn.',
    'hsk1_qing': 'Qǐng nǐ kàn zhège zì.',
    'hsk1_qu': 'Jīntiān wǒ bù qù xuéxiào.',
    'hsk1_re': 'Shuǐ hěn rè.',
    'hsk1_ren': 'Nàge rén shì wǒ bàba.',
    'hsk1_renshi': 'Nǐ rènshi tā ma?',
    'hsk1_san': 'Zhuōzi shàng yǒu sān gè bēizi.',
    'hsk1_shangdian': 'Shāngdiàn lǐ yǒu shuǐguǒ ma?',
    'hsk1_shang': 'Bēizi zài zhuōzi shàng.',
    'hsk1_shangwu': 'Wǒ shàngwǔ qù xuéxiào.',
    'hsk1_shao': 'Wǒmen xuéxiào rén hěn shǎo.',
    'hsk1_shei': 'Shéi shì nǐ de lǎoshī?',
    'hsk1_shenme': 'Nǐ zài xiě shénme?',
    'hsk1_shi2': 'Shí diǎn wǒmen qù fàndiàn.',
    'hsk1_shihou': 'Wǒ xiǎo de shíhou zhù zài Běijīng.',
    'hsk1_shi': 'Zhè shì wǒ māma.',
    'hsk1_shu': 'Nǐ de shū zài zhuōzi shàng.',
    'hsk1_shui': 'Wǒ xiǎng hē shuǐ.',
    'hsk1_shuiguo': 'Wǒ mǎi le yī xiē shuǐguǒ.',
    'hsk1_shuijiao': 'Tā shí diǎn shuìjiào.',
    'hsk1_shuo': 'Nǐ huì shuō Hànyǔ ma?',
    'hsk1_si': 'Sì diǎn wǒ huí jiā.',
    'hsk1_sui': 'Wǒ māma sì shí suì.',
    'hsk1_ta': 'Tā shì wǒ de péngyou.',
    'hsk1_ta2': 'Tā xǐhuan hē chá.',
    'hsk1_tai': 'Wǒ de zhuōzi tài xiǎo le.',
    'hsk1_tianqi': 'Běijīng tiānqì zěnmeyàng?',
    'hsk1_ting': 'Wǒ xǐhuan tīng Hànyǔ.',
    'hsk1_tongxue': 'Wǒ de tóngxué dōu zài Běijīng.',
    'hsk1_wei': 'Wèi, nǐ zài jiā ma?',
    'hsk1_wo': 'Wǒ bù shì xuésheng.',
    'hsk1_women': 'Wǒmen dōu shì Zhōngguó rén.',
    'hsk1_wu': 'Wǔ diǎn wǒ qù fàndiàn.',
    'hsk1_xihuan': 'Wǒ xǐhuan zhège bēizi.',
    'hsk1_xia': 'Shū zài zhuōzi xiàmiàn.',
    'hsk1_xiawu': 'Xiàwǔ wǒ xiǎng kàn diànyǐng.',
    'hsk1_xiayu': 'Jīntiān xià yǔ, wǒmen bù qù xuéxiào.',
    'hsk1_xiansheng': 'Xiānshēng, qǐng zuò.',
    'hsk1_xianzai': 'Xiànzài wǒmen qù fàndiàn.',
    'hsk1_xiang': 'Nǐ xiǎng hē shuǐ ma?',
    'hsk1_xiao': 'Zhège bēizi hěn xiǎo.',
    'hsk1_xiaojie': 'Xiǎojie, qǐng zuò.',
    'hsk1_xie': 'Wǒ mǎi le yī xiē shū.',
    'hsk1_xie2': 'Qǐng xiě nǐ de míngzi.',
    'hsk1_xiexie': 'Xièxie nǐ lái wǒ jiā.',
    'hsk1_xingqi': 'Jīntiān xīngqī sān.',
    'hsk1_xuesheng': 'Tā shì wǒ de xuésheng.',
    'hsk1_xuexi': 'Tā zài xuéxiào xuéxí Hànyǔ.',
    'hsk1_xuexiao': 'Xuéxiào lǐ yǒu hěn duō xuésheng.',
    'hsk1_yi': 'Wǒ yǒu yī gè péngyou.',
    'hsk1_yidianr': 'Wǒ xiǎng hē yīdiǎnr shuǐ.',
    'hsk1_yifu': 'Tā de yīfu hěn piàoliang.',
    'hsk1_yisheng': 'Yīshēng zài yīyuàn ma?',
    'hsk1_yiyuan': 'Wǒ māma zài yīyuàn.',
    'hsk1_yizi': 'Lǎoshī zuò zài yǐzi shàng.',
    'hsk1_you': 'Xuéxiào lǐ yǒu hěn duō shū.',
    'hsk1_yue': 'Èr yuè Běijīng hěn lěng.',
    'hsk1_zai': 'Wǒ bàba zài Běijīng.',
    'hsk1_zaijian': 'Wǒmen jīntiān xiàwǔ zàijiàn.',
    'hsk1_zenme': 'Nǐ zěnme qù xuéxiào?',
    'hsk1_zenmeyang': 'Nǐ māma zěnmeyàng?',
    'hsk1_zhe': 'Zhè shì wǒ de diànnǎo.',
    'hsk1_zhongguo': 'Tā zài Zhōngguó xuéxí Hànyǔ.',
    'hsk1_zhongwu': 'Zhōngwǔ wǒmen qù fàndiàn.',
    'hsk1_zhu': 'Wǒ zhù zài xuéxiào hòumiàn.',
    'hsk1_zhuozi': 'Zhuōzi shàng yǒu yī běn shū.',
    'hsk1_zi': 'Zhège zì zěnme dú?',
    'hsk1_zuotian': 'Zuótiān wǒmen kàn diànyǐng le.',
    'hsk1_zuo2': 'Nǐ zuò chūzūchē ma?',
    'hsk1_zuo': 'Māma zài jiā zuò mǐfàn.',
}

HSK1_VOCAB = [
    entry[:5] + (AUDIO_SENTENCE_PINYIN[entry[0]],) + entry[5:7]
    + (READING_SENTENCE_PINYIN[entry[0]],) + entry[7:]
    for entry in HSK1_VOCAB
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
    {"name": "WordSound"},
    {"name": "AudioSentenceCN"},
    {"name": "AudioSentenceSound"},
    {"name": "AudioSentencePY"},
    {"name": "AudioSentenceDE"},
    {"name": "ReadingSentenceCN"},
    {"name": "ReadingSentenceSound"},
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
<div class="audio-control">{{ReadingSentenceSound}}</div>
<div class="hint">Audio wiederholen</div>
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
<div class="audio-control">{{WordSound}}</div>
<div class="hint">Aussprache wiederholen</div>
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
        "WordSound",
        "AudioSentenceCN",
        "AudioSentenceSound",
        "AudioSentencePY",
        "AudioSentenceDE",
        "ReadingSentenceCN",
        "ReadingSentenceSound",
        "ReadingSentencePY",
        "ReadingSentenceDE",
    ]
    if [field["name"] for field in FIELDS] != expected_fields:
        raise ValueError("The model must have exactly the twelve expected fields.")

    if [template["name"] for template in TEMPLATES] != [
            "1. Leseverstehen", "2. Hörverstehen", "3. Wortschatz"]:
        raise ValueError("The model must contain reading, listening, and vocabulary templates.")

    reading, listening, vocabulary = TEMPLATES
    reading_front_fields = re.findall(r"{{([^}]+)}}", reading["qfmt"])
    if reading_front_fields != ["ReadingSentenceCN"] or reading["qfmt"].strip() != (
            '<div class="sentence">{{ReadingSentenceCN}}</div>'):
        raise ValueError("The reading-card front must show only its reading sentence.")
    if (
            "{{ReadingSentenceSound}}" not in reading["afmt"]
            or "{{ReadingSentencePY}}" not in reading["afmt"]
            or "{{Hanzi}}" not in reading["afmt"]
            or "{{Meaning}}" not in reading["afmt"]
    ):
        raise ValueError("The reading-card back must reveal its pinyin and focus word.")
    listening_front_fields = re.findall(r"{{([^}]+)}}", listening["qfmt"])
    if listening_front_fields != ["AudioSentenceSound"]:
        raise ValueError("The listening-card front must show only the embedded sound control.")
    if (
            "{{AudioSentenceCN}}" not in listening["afmt"]
            or "{{Hanzi}}" not in listening["afmt"]
            or "{{Meaning}}" not in listening["afmt"]
    ):
        raise ValueError("The listening-card back must reveal the sentence and focus word.")
    vocabulary_front_fields = re.findall(r"{{([^}]+)}}", vocabulary["qfmt"])
    if vocabulary_front_fields != ["Hanzi"]:
        raise ValueError("The vocabulary-card front must show only the isolated word.")
    if (
            "{{WordSound}}" not in vocabulary["afmt"]
            or "{{Pinyin}}" not in vocabulary["afmt"]
            or "{{Meaning}}" not in vocabulary["afmt"]
    ):
        raise ValueError("The vocabulary-card back must reveal pronunciation, pinyin, and meaning.")



def validate_vocabulary() -> None:
    """Fail early if this self-contained source no longer describes HSK 1.0."""
    if len(OFFICIAL_HSK1_WORDS) != 150 or len(HSK1_VOCAB) != 150:
        raise ValueError("HSK 1.0 must contain exactly 150 vocabulary entries.")

    words = [entry[1] for entry in HSK1_VOCAB]
    ids = [entry[0] for entry in HSK1_VOCAB]
    if tuple(words) != OFFICIAL_HSK1_WORDS:
        raise ValueError("HSK1_VOCAB does not match the official HSK 1.0 order.")
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
        if not all((word, pinyin, german, audio_zh, audio_py, audio_de, reading_zh,
                    reading_py, reading_de, filename)):
            raise ValueError(f"Blank field in vocabulary entry {entry[0]!r}.")
        if filename != f"{entry[0]}.mp3":
            raise ValueError(f"Unexpected audio filename for {entry[0]!r}.")
        if audio_zh.strip() == reading_zh.strip():
            raise ValueError(
                f"Reading sentence must differ from audio sentence for {entry[0]!r}."
            )
        if word not in audio_zh or word not in reading_zh:
            raise ValueError(f"Focus word must appear in both example sentences for {entry[0]!r}.")
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
            f"Generated package embeds {len(embedded_audio)} expected audio files; "
            "expected all 450."
        )


def build_deck(output_path: Path) -> None:
    """Create and verify the package with listening, reading, and word MP3s embedded."""
    validate_deck_structure()
    validate_vocabulary()
    model = genanki.Model(MODEL_ID, DECK_NAME, fields=FIELDS, templates=TEMPLATES, css=CSS)
    deck = genanki.Deck(DECK_ID, DECK_NAME)
    media_files = []

    for (vocab_id, chinese, pinyin, german, audio_zh, audio_py, audio_de, reading_zh,
         reading_py, reading_de, filename) in HSK1_VOCAB:
        audio_path = AUDIO_DIR / filename
        reading_filename = f"{vocab_id}_reading.mp3"
        reading_audio_path = AUDIO_DIR / reading_filename
        word_filename = f"{vocab_id}_word.mp3"
        word_audio_path = AUDIO_DIR / word_filename
        if not audio_path.is_file():
            raise FileNotFoundError(f"Required listening audio is missing: {audio_path}")
        if not reading_audio_path.is_file():
            raise FileNotFoundError(f"Required reading audio is missing: {reading_audio_path}")
        if not word_audio_path.is_file():
            raise FileNotFoundError(f"Required word audio is missing: {word_audio_path}")
        media_files.extend((str(audio_path), str(reading_audio_path), str(word_audio_path)))

        deck.add_note(genanki.Note(
            model=model,
            guid=genanki.guid_for("hsk1-german-standalone", vocab_id),
            fields=[
                chinese, pinyin, german, f"[sound:{word_filename}]",
                audio_zh, f"[sound:{filename}]", audio_py, audio_de,
                reading_zh, f"[sound:{reading_filename}]", reading_py, reading_de,
            ],
        ))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file(str(output_path))
    validate_generated_package(output_path, {path.name for path in map(Path, media_files)})

    print(f"Created {output_path}")
    print("  150 vocabulary entries -> 450 cards (3 templates per entry)")
    print(f"  Audio files embedded: {len(media_files)}/450")



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
