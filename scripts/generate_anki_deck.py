#!/usr/bin/env python3
"""
Generate an Anki deck (.apkg) for HSK 2 vocabulary.

The deck contains three card types per vocabulary entry:
  1. Word card   – front: Chinese character(s); back: pinyin + English + audio + sentence
  2. Sentence card – front: example sentence + audio; back: translation + word + audio (replay)
  3. Audio card  – front: audio only; back: Chinese + pinyin + English + sentence

Audio files are taken from audio/ at the repository root (one MP3 per vocab entry
that contains the spoken example sentence).

Usage:
    python3 scripts/generate_anki_deck.py [--output OUTPUT]

    --output  Path for the .apkg file (default: hsk2.apkg next to this script)

Requirements:
    pip install genanki
"""

import argparse
import os
import random
import sys

try:
    import genanki
except ImportError:
    sys.exit("genanki is required: pip install genanki")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
AUDIO_DIR = os.path.join(REPO_ROOT, "audio")

# ---------------------------------------------------------------------------
# HSK 2 vocabulary — mirrors VocabData.kt
# Fields: (id, chinese, pinyin, english, sentence, sentence_pinyin, sentence_english)
# ---------------------------------------------------------------------------
HSK2_VOCAB = [
    ("hsk2_bangzhu",       "帮助", "bāngzhù",        "help",
     "谢谢你帮助我。",               "Xièxie nǐ bāngzhù wǒ.",                    "Thank you for helping me."),
    ("hsk2_bi",            "比",   "bǐ",              "compare / than",
     "今天比昨天冷。",               "Jīntiān bǐ zuótiān lěng.",                 "Today is colder than yesterday."),
    ("hsk2_bie",           "别",   "bié",             "don't",
     "别忘了带水。",                 "Bié wàng le dài shuǐ.",                    "Don't forget to bring water."),
    ("hsk2_chuan",         "穿",   "chuān",           "wear / put on",
     "今天很冷，多穿衣服。",         "Jīntiān hěn lěng, duō chuān yīfu.",        "It's cold today, wear more clothes."),
    ("hsk2_cong",          "从",   "cóng",            "from",
     "我从北京来。",                 "Wǒ cóng Běijīng lái.",                     "I come from Beijing."),
    ("hsk2_danshi",        "但是", "dànshì",          "but / however",
     "我想去，但是没有时间。",       "Wǒ xiǎng qù, dànshì méiyǒu shíjiān.",     "I want to go, but I don't have time."),
    ("hsk2_difang",        "地方", "dìfāng",          "place",
     "北京是一个好地方。",           "Běijīng shì yīgè hǎo dìfāng.",            "Beijing is a great place."),
    ("hsk2_du",            "读",   "dú",              "read (aloud)",
     "他喜欢读书。",                 "Tā xǐhuān dú shū.",                        "He likes reading books."),
    ("hsk2_dui",           "对",   "duì",             "correct / right",
     "你说的对。",                   "Nǐ shuō de duì.",                          "What you said is correct."),
    ("hsk2_fangjian",      "房间", "fángjiān",        "room",
     "我的房间很小。",               "Wǒ de fángjiān hěn xiǎo.",                 "My room is very small."),
    ("hsk2_gaosu",         "告诉", "gàosu",           "tell",
     "请告诉我你的名字。",           "Qǐng gàosu wǒ nǐ de míngzi.",             "Please tell me your name."),
    ("hsk2_gen",           "跟",   "gēn",             "with / follow",
     "我跟朋友一起去。",             "Wǒ gēn péngyou yīqǐ qù.",                 "I go together with my friend."),
    ("hsk2_hai",           "还",   "hái",             "still / also",
     "他还在学校。",                 "Tā hái zài xuéxiào.",                      "He is still at school."),
    ("hsk2_haizi",         "孩子", "háizi",           "child",
     "这个孩子很聪明。",             "Zhège háizi hěn cōngming.",                "This child is very smart."),
    ("hsk2_huanying",      "欢迎", "huānyíng",        "welcome",
     "欢迎来到我家。",               "Huānyíng lái dào wǒ jiā.",                 "Welcome to my home."),
    ("hsk2_huozhe",        "或者", "huòzhě",          "or",
     "你喝茶或者咖啡？",             "Nǐ hē chá huòzhě kāfēi?",                 "Do you drink tea or coffee?"),
    ("hsk2_jichang",       "机场", "jīchǎng",         "airport",
     "我去机场接朋友。",             "Wǒ qù jīchǎng jiē péngyou.",              "I'm going to the airport to pick up a friend."),
    ("hsk2_jide",          "记得", "jìde",            "remember",
     "你记得我的名字吗？",           "Nǐ jìde wǒ de míngzi ma?",                "Do you remember my name?"),
    ("hsk2_juede",         "觉得", "juéde",           "feel / think",
     "我觉得今天很冷。",             "Wǒ juéde jīntiān hěn lěng.",              "I feel today is very cold."),
    ("hsk2_kaishi",        "开始", "kāishǐ",          "begin / start",
     "我们开始学习吧。",             "Wǒmen kāishǐ xuéxí ba.",                  "Let's start studying."),
    ("hsk2_li",            "离",   "lí",              "away from / distance",
     "学校离我家很近。",             "Xuéxiào lí wǒ jiā hěn jìn.",              "School is very close to my home."),
    ("hsk2_lianxi",        "练习", "liànxí",          "practice",
     "每天练习说汉语。",             "Měitiān liànxí shuō Hànyǔ.",              "Practice speaking Chinese every day."),
    ("hsk2_luyou",         "旅游", "lǚyóu",           "travel / tourism",
     "我喜欢旅游，看新地方。",       "Wǒ xǐhuān lǚyóu, kàn xīn dìfāng.",       "I like traveling and seeing new places."),
    ("hsk2_nan",           "难",   "nán",             "difficult",
     "汉语有一点难。",               "Hànyǔ yǒu yīdiǎn nán.",                   "Chinese is a little difficult."),
    ("hsk2_piao",          "票",   "piào",            "ticket",
     "我买了两张电影票。",           "Wǒ mǎi le liǎng zhāng diànyǐng piào.",    "I bought two movie tickets."),
    ("hsk2_ren",           "认识", "rènshi",          "know (a person)",
     "我认识她，她是我朋友。",       "Wǒ rènshi tā, tā shì wǒ péngyou.",        "I know her, she is my friend."),
    ("hsk2_shenti",        "身体", "shēntǐ",          "body / health",
     "身体健康最重要。",             "Shēntǐ jiànkāng zuì zhòngyào.",            "Good health is the most important."),
    ("hsk2_shijian",       "时间", "shíjiān",         "time",
     "我没有时间看电视。",           "Wǒ méiyǒu shíjiān kàn diànshì.",          "I don't have time to watch TV."),
    ("hsk2_xihuan",        "喜欢", "xǐhuān",          "like / enjoy",
     "我喜欢学习汉语。",             "Wǒ xǐhuān xuéxí Hànyǔ.",                  "I like studying Chinese."),
    ("hsk2_xiao",          "笑",   "xiào",            "laugh / smile",
     "他总是笑着说话。",             "Tā zǒng shì xiào zhe shuōhuà.",           "He always speaks with a smile."),
    ("hsk2_yiqi",          "一起", "yīqǐ",            "together",
     "我们一起去吃饭吧。",           "Wǒmen yīqǐ qù chīfàn ba.",                "Let's go eat together."),
    ("hsk2_zhunbei",       "准备", "zhǔnbèi",         "prepare",
     "我在准备考试。",               "Wǒ zài zhǔnbèi kǎoshì.",                  "I am preparing for an exam."),
    ("hsk2_zuo",           "坐",   "zuò",             "sit / ride (transport)",
     "我坐公共汽车去学校。",         "Wǒ zuò gōnggòng qìchē qù xuéxiào.",       "I ride the bus to school."),
    ("hsk2_ayi",           "阿姨", "āyí",             "aunt / auntie",
     "我的阿姨住在上海。",           "Wǒ de āyí zhù zài Shànghǎi.",             "My aunt lives in Shanghai."),
    ("hsk2_ba",            "吧",   "ba",              "suggestion particle",
     "我们去看电影吧。",             "Wǒmen qù kàn diànyǐng ba.",               "Let's go watch a movie."),
    ("hsk2_ban",           "半",   "bàn",             "half",
     "现在是七点半。",               "Xiànzài shì qī diǎn bàn.",                "It is now seven thirty."),
    ("hsk2_banfa",         "办法", "bànfǎ",           "method / way",
     "我没有办法去。",               "Wǒ méiyǒu bànfǎ qù.",                     "I have no way to go."),
    ("hsk2_bang",          "帮",   "bāng",            "help",
     "请帮我拿一下包。",             "Qǐng bāng wǒ ná yīxià bāo.",              "Please help me hold the bag."),
    ("hsk2_bieren",        "别人", "biérén",          "other people",
     "不要总是担心别人怎么看你。",   "Bùyào zǒng shì dānxīn biérén zěnme kàn nǐ.", "Don't always worry about what others think of you."),
    ("hsk2_binguan",       "宾馆", "bīnguǎn",         "hotel",
     "我住在一家宾馆里。",           "Wǒ zhù zài yījiā bīnguǎn lǐ.",            "I'm staying at a hotel."),
    ("hsk2_bingxiang",     "冰箱", "bīngxiāng",       "refrigerator",
     "牛奶在冰箱里。",               "Niúnǎi zài bīngxiāng lǐ.",                "The milk is in the refrigerator."),
    ("hsk2_cai2",          "才",   "cái",             "just / only then",
     "他才来了。",                   "Tā cái lái le.",                           "He just arrived."),
    ("hsk2_cha2",          "差",   "chà",             "not good enough / differ",
     "我的汉语还差得很远。",         "Wǒ de Hànyǔ hái chà de hěn yuǎn.",        "My Chinese is still far from good enough."),
    ("hsk2_chang",         "长",   "cháng",           "long",
     "这条路很长，要走很久。",       "Zhè tiáo lù hěn cháng, yào zǒu hěn jiǔ.", "This road is very long; it takes a long time to walk."),
    ("hsk2_changge",       "唱歌", "chàng gē",        "sing a song",
     "她很喜欢唱歌。",               "Tā hěn xǐhuān chàng gē.",                 "She loves singing."),
    ("hsk2_chaoshi",       "超市", "chāoshì",         "supermarket",
     "我去超市买水果和蔬菜。",       "Wǒ qù chāoshì mǎi shuǐguǒ hé shūcài.",   "I go to the supermarket to buy fruit and vegetables."),
    ("hsk2_chulai",        "出来", "chū lái",         "come out",
     "请你出来一下。",               "Qǐng nǐ chū lái yīxià.",                  "Please come out for a moment."),
    ("hsk2_da2",           "打",   "dǎ",              "hit / play (sport)",
     "他喜欢打篮球。",               "Tā xǐhuān dǎ lánqiú.",                    "He likes playing basketball."),
    ("hsk2_dasuan",        "打算", "dǎsuàn",          "plan / intend",
     "你打算去哪里旅游？",           "Nǐ dǎsuàn qù nǎlǐ lǚyóu?",               "Where do you plan to travel?"),
    ("hsk2_dangran",       "当然", "dāngrán",         "of course",
     "当然，我很乐意帮你。",         "Dāngrán, wǒ hěn lèyì bāng nǐ.",           "Of course, I'm happy to help you."),
    ("hsk2_ditie",         "地铁", "dìtiě",           "subway / metro",
     "我每天坐地铁去上班。",         "Wǒ měitiān zuò dìtiě qù shàngbān.",       "I take the subway to work every day."),
    ("hsk2_dong",          "动",   "dòng",            "move",
     "请不要动，我帮你拍照。",       "Qǐng bùyào dòng, wǒ bāng nǐ pāizhào.",   "Please don't move; I'll take a photo for you."),
    ("hsk2_fa",            "发",   "fā",              "send / emit",
     "我给你发一条消息。",           "Wǒ gěi nǐ fā yī tiáo xiāoxi.",            "I'll send you a message."),
    ("hsk2_fangbian",      "方便", "fāngbiàn",        "convenient",
     "住在学校附近很方便。",         "Zhù zài xuéxiào fùjìn hěn fāngbiàn.",     "Living near school is very convenient."),
    ("hsk2_fang",          "放",   "fàng",            "put / place",
     "请把书放在桌子上。",           "Qǐng bǎ shū fàng zài zhuōzi shàng.",      "Please put the book on the table."),
    ("hsk2_fen",           "分",   "fēn",             "minute / cent / divide",
     "我们还有十分钟。",             "Wǒmen hái yǒu shí fēnzhōng.",             "We still have ten minutes."),
    ("hsk2_fuwuyuan",      "服务员", "fúwùyuán",      "waiter / service staff",
     "服务员，请给我一杯水。",       "Fúwùyuán, qǐng gěi wǒ yī bēi shuǐ.",     "Waiter, please bring me a glass of water."),
    ("hsk2_gei",           "给",   "gěi",             "give / for / to",
     "妈妈给我买了一个礼物。",       "Māma gěi wǒ mǎi le yīgè lǐwù.",          "Mom bought me a gift."),
    ("hsk2_geng",          "更",   "gèng",            "even more",
     "今天比昨天更冷。",             "Jīntiān bǐ zuótiān gèng lěng.",           "Today is even colder than yesterday."),
    ("hsk2_gonggongqiche", "公共汽车", "gōnggòng qìchē", "public bus",
     "我坐公共汽车去学校。",         "Wǒ zuò gōnggòng qìchē qù xuéxiào.",       "I take the public bus to school."),
    ("hsk2_gongsi",        "公司", "gōngsī",          "company",
     "他在一家大公司工作。",         "Tā zài yījiā dà gōngsī gōngzuò.",         "He works at a large company."),
    ("hsk2_gushi",         "故事", "gùshi",           "story",
     "妈妈每天晚上给我讲故事。",     "Māma měitiān wǎnshàng gěi wǒ jiǎng gùshi.", "Mom tells me a story every evening."),
    ("hsk2_guanxi",        "关系", "guānxi",          "relationship / connection",
     "我们的关系很好。",             "Wǒmen de guānxi hěn hǎo.",                 "We have a good relationship."),
    ("hsk2_gui",           "贵",   "guì",             "expensive",
     "这件衣服很贵，我买不起。",     "Zhè jiàn yīfu hěn guì, wǒ mǎi bu qǐ.",   "This piece of clothing is very expensive; I can't afford it."),
    ("hsk2_hei",           "黑",   "hēi",             "black",
     "他有一只黑猫。",               "Tā yǒu yī zhī hēi māo.",                  "He has a black cat."),
    ("hsk2_houlai",        "后来", "hòulái",          "later / afterwards",
     "他先工作，后来去吃饭。",       "Tā xiān gōngzuò, hòulái qù chīfàn.",      "He worked first, then went to eat."),
    ("hsk2_huilai",        "回来", "huí lái",         "come back",
     "他出去了，等一下就回来。",     "Tā chūqù le, děng yīxià jiù huí lái.",    "He went out and will be back soon."),
    ("hsk2_haishi",        "还是", "háishi",          "or (in questions) / still",
     "你喝茶还是咖啡？",             "Nǐ hē chá háishi kāfēi?",                 "Do you drink tea or coffee?"),
    ("hsk2_jiandan",       "简单", "jiǎndān",         "simple / easy",
     "这道题很简单。",               "Zhè dào tí hěn jiǎndān.",                 "This question is very simple."),
    ("hsk2_jian",          "件",   "jiàn",            "measure word (for clothes / matters)",
     "我买了两件衣服。",             "Wǒ mǎi le liǎng jiàn yīfu.",              "I bought two pieces of clothing."),
    ("hsk2_keyi",          "可以", "kěyǐ",            "can / may",
     "我可以问你一个问题吗？",       "Wǒ kěyǐ wèn nǐ yīgè wèntí ma?",          "May I ask you a question?"),
    ("hsk2_liaotian",      "聊天", "liáotiān",        "chat",
     "我们在咖啡馆聊天。",           "Wǒmen zài kāfēiguǎn liáotiān.",            "We are chatting in the café."),
    ("hsk2_mai",           "卖",   "mài",             "sell",
     "这家店卖新鲜水果。",           "Zhè jiā diàn mài xīnxiān shuǐguǒ.",       "This shop sells fresh fruit."),
    ("hsk2_mianbao",       "面包", "miànbāo",         "bread",
     "我早上吃面包和鸡蛋。",         "Wǒ zǎoshàng chī miànbāo hé jīdàn.",       "I eat bread and eggs in the morning."),
    ("hsk2_miantiao",      "面条", "miàntiáo",        "noodles",
     "我最喜欢吃面条。",             "Wǒ zuì xǐhuān chī miàntiáo.",             "I like eating noodles the most."),
    ("hsk2_mingbai",       "明白", "míngbai",         "understand / clear",
     "你明白我的意思吗？",           "Nǐ míngbai wǒ de yìsi ma?",               "Do you understand what I mean?"),
    ("hsk2_name",          "那么", "nàme",            "then / so",
     "那么，我们明天见吧。",         "Nàme, wǒmen míngtiān jiàn ba.",            "So, let's meet tomorrow then."),
    ("hsk2_neng",          "能",   "néng",            "can / be able to",
     "你能帮我吗？",                 "Nǐ néng bāng wǒ ma?",                     "Can you help me?"),
    ("hsk2_pang",          "胖",   "pàng",            "fat / chubby",
     "他觉得自己有点胖，想减肥。",   "Tā juéde zìjǐ yǒudiǎn pàng, xiǎng jiǎnféi.", "He thinks he is a bit fat and wants to lose weight."),
    ("hsk2_putonghua",     "普通话", "pǔtōnghuà",     "Mandarin Chinese",
     "在中国，人们说普通话。",       "Zài Zhōngguó, rénmen shuō pǔtōnghuà.",    "In China, people speak Mandarin."),
    ("hsk2_qishi",         "其实", "qíshí",           "actually / in fact",
     "其实，他是一个很好的人。",     "Qíshí, tā shì yīgè hěn hǎo de rén.",      "Actually, he is a very good person."),
    ("hsk2_qi",            "骑",   "qí",              "ride (bicycle / horse)",
     "我骑自行车去学校。",           "Wǒ qí zìxíngchē qù xuéxiào.",             "I ride a bicycle to school."),
    ("hsk2_rang",          "让",   "ràng",            "let / allow / cause",
     "请让我先说。",                 "Qǐng ràng wǒ xiān shuō.",                 "Please let me speak first."),
    ("hsk2_ruguo",         "如果", "rúguǒ",           "if",
     "如果明天下雨，我就不去了。",   "Rúguǒ míngtiān xià yǔ, wǒ jiù bù qù le.", "If it rains tomorrow, I won't go."),
    ("hsk2_shengqi",       "生气", "shēngqì",         "angry",
     "别生气，这件事不重要。",       "Bié shēngqì, zhè jiàn shì bù zhòngyào.", "Don't be angry; this matter is not important."),
    ("hsk2_shouji",        "手机", "shǒujī",          "mobile phone",
     "我的手机没有电了。",           "Wǒ de shǒujī méiyǒu diàn le.",            "My phone is out of battery."),
    ("hsk2_song",          "送",   "sòng",            "send / give as gift",
     "他送给我一本书。",             "Tā sòng gěi wǒ yī běn shū.",              "He gave me a book as a gift."),
    ("hsk2_suoyi",         "所以", "suǒyǐ",           "so / therefore",
     "天气很冷，所以我穿了厚衣服。", "Tiānqì hěn lěng, suǒyǐ wǒ chuān le hòu yīfu.", "It's very cold, so I wore thick clothes."),
    ("hsk2_tebie",         "特别", "tèbié",           "special / especially",
     "这家餐厅的菜特别好吃。",       "Zhè jiā cāntīng de cài tèbié hǎochī.",    "This restaurant's dishes are especially delicious."),
    ("hsk2_tian",          "甜",   "tián",            "sweet",
     "这个蛋糕很甜。",               "Zhège dàngāo hěn tián.",                  "This cake is very sweet."),
    ("hsk2_tingshu",       "听说", "tīng shuō",       "hear that / it is said",
     "听说他要去北京工作。",         "Tīng shuō tā yào qù Běijīng gōngzuò.",    "I heard that he is going to work in Beijing."),
    ("hsk2_tongshi",       "同事", "tóngshì",         "colleague",
     "他是我的同事，我们一起工作。", "Tā shì wǒ de tóngshì, wǒmen yīqǐ gōngzuò.", "He is my colleague; we work together."),
    ("hsk2_toufa",         "头发", "tóufa",           "hair",
     "她有一头漂亮的长头发。",       "Tā yǒu yī tóu piàoliang de cháng tóufa.", "She has beautiful long hair."),
    ("hsk2_weishenme",     "为什么", "wèishénme",     "why",
     "你为什么学习汉语？",           "Nǐ wèishénme xuéxí Hànyǔ?",              "Why are you learning Chinese?"),
    ("hsk2_wenhua",        "文化", "wénhuà",          "culture",
     "中国文化非常丰富。",           "Zhōngguó wénhuà fēicháng fēngfù.",         "Chinese culture is very rich."),
    ("hsk2_wen",           "问",   "wèn",             "ask",
     "我可以问你一个问题吗？",       "Wǒ kěyǐ wèn nǐ yīgè wèntí ma?",          "May I ask you a question?"),
    ("hsk2_wenti",         "问题", "wèntí",           "question / problem",
     "这道题有问题，我不会做。",     "Zhè dào tí yǒu wèntí, wǒ bù huì zuò.",   "There is a problem with this question; I can't solve it."),
    ("hsk2_xi",            "洗",   "xǐ",              "wash",
     "我每天早上洗脸。",             "Wǒ měitiān zǎoshàng xǐ liǎn.",            "I wash my face every morning."),
    ("hsk2_xiaoshi",       "小时", "xiǎoshí",         "hour",
     "我每天学习两个小时汉语。",     "Wǒ měitiān xuéxí liǎng gè xiǎoshí Hànyǔ.", "I study Chinese for two hours every day."),
    ("hsk2_xie",           "写",   "xiě",             "write",
     "请你写一下你的名字。",         "Qǐng nǐ xiě yīxià nǐ de míngzi.",         "Please write down your name."),
    ("hsk2_xinglixiang",   "行李箱", "xíngli xiāng",  "suitcase",
     "我的行李箱太重了。",           "Wǒ de xíngli xiāng tài zhòng le.",         "My suitcase is too heavy."),
    ("hsk2_yihou",         "以后", "yǐhòu",           "after / in the future",
     "以后我想去中国旅游。",         "Yǐhòu wǒ xiǎng qù Zhōngguó lǚyóu.",      "In the future I want to travel to China."),
    ("hsk2_yiqian",        "以前", "yǐqián",          "before / in the past",
     "以前我不喜欢吃蔬菜。",         "Yǐqián wǒ bù xǐhuān chī shūcài.",         "Before, I didn't like eating vegetables."),
    ("hsk2_yijing",        "已经", "yǐjīng",          "already",
     "他已经回家了。",               "Tā yǐjīng huí jiā le.",                    "He has already gone home."),
    ("hsk2_yong",          "用",   "yòng",            "use",
     "你用什么语言说话？",           "Nǐ yòng shénme yǔyán shuōhuà?",           "What language do you speak?"),
    ("hsk2_youming",       "有名", "yǒumíng",         "famous",
     "这家餐厅很有名。",             "Zhè jiā cāntīng hěn yǒumíng.",             "This restaurant is very famous."),
    ("hsk2_zai2",          "再",   "zài",             "again / once more",
     "请再说一遍。",                 "Qǐng zài shuō yī biàn.",                  "Please say it one more time."),
    ("hsk2_zhang",         "张",   "zhāng",           "measure word (for flat things)",
     "我买了两张电影票。",           "Wǒ mǎi le liǎng zhāng diànyǐng piào.",    "I bought two movie tickets."),
    ("hsk2_zhao",          "找",   "zhǎo",            "look for / find",
     "我在找我的钥匙。",             "Wǒ zài zhǎo wǒ de yàoshi.",               "I am looking for my keys."),
    ("hsk2_zhen",          "真",   "zhēn",            "true / really",
     "这个故事是真的吗？",           "Zhège gùshi shì zhēn de ma?",             "Is this story true?"),
    ("hsk2_zhengzai",      "正在", "zhèngzài",        "currently / in the process of",
     "他正在学习汉语。",             "Tā zhèngzài xuéxí Hànyǔ.",                "He is currently studying Chinese."),
    ("hsk2_zhidao",        "知道", "zhīdào",          "know",
     "你知道他住在哪里吗？",         "Nǐ zhīdào tā zhù zài nǎlǐ ma?",           "Do you know where he lives?"),
    ("hsk2_zhi",           "只",   "zhǐ",             "only / just",
     "我只喝水，不喝咖啡。",         "Wǒ zhǐ hē shuǐ, bù hē kāfēi.",           "I only drink water, not coffee."),
    ("hsk2_zhongyao",      "重要", "zhòngyào",        "important",
     "健康比金钱更重要。",           "Jiànkāng bǐ jīnqián gèng zhòngyào.",      "Health is more important than money."),
    ("hsk2_shuohua",       "说话", "shuōhuà",         "speak / talk",
     "上课的时候不要说话。",         "Shàngkè de shíhòu bùyào shuōhuà.",        "Don't talk during class."),
    ("hsk2_man",           "慢",   "màn",             "slow",
     "请说慢一点，我听不清楚。",     "Qǐng shuō màn yīdiǎn, wǒ tīng bu qīngchǔ.", "Please speak more slowly; I can't hear clearly."),
    ("hsk2_kuai2",         "快",   "kuài",            "fast / quick",
     "他走路很快。",                 "Tā zǒulù hěn kuài.",                       "He walks very fast."),
    ("hsk2_xin",           "新",   "xīn",             "new",
     "我买了一本新书。",             "Wǒ mǎi le yī běn xīn shū.",               "I bought a new book."),
    ("hsk2_leng",          "冷",   "lěng",            "cold",
     "今天很冷，多穿衣服。",         "Jīntiān hěn lěng, duō chuān yīfu.",        "It's very cold today, wear more clothes."),
    ("hsk2_bai",           "白",   "bái",             "white",
     "她穿了一件白衬衫。",           "Tā chuān le yī jiàn bái chènshān.",        "She wore a white shirt."),
    ("hsk2_bai2",          "百",   "bǎi",             "hundred",
     "这本书一百页。",               "Zhè běn shū yī bǎi yè.",                  "This book has one hundred pages."),
    ("hsk2_baozhi",        "报纸", "bàozhǐ",          "newspaper",
     "我爸爸每天早上看报纸。",       "Wǒ bàba měitiān zǎoshàng kàn bàozhǐ.",    "My dad reads the newspaper every morning."),
    ("hsk2_ci",            "次",   "cì",              "time (occurrence)",
     "我去过北京两次。",             "Wǒ qùguò Běijīng liǎng cì.",              "I have been to Beijing twice."),
    ("hsk2_cuo",           "错",   "cuò",             "wrong / mistake",
     "对不起，我说错了。",           "Duìbuqǐ, wǒ shuō cuò le.",                "Sorry, I said it wrong."),
    ("hsk2_dajia",         "大家", "dàjiā",           "everyone",
     "大家好，我叫李明。",           "Dàjiā hǎo, wǒ jiào Lǐ Míng.",             "Hello everyone, my name is Li Ming."),
    ("hsk2_ditu",          "地图", "dìtú",            "map",
     "请给我看一下地图。",           "Qǐng gěi wǒ kàn yīxià dìtú.",             "Please show me the map."),
    ("hsk2_diyi",          "第一", "dì yī",           "first / number one",
     "他是班里第一名。",             "Tā shì bān lǐ dì yī míng.",               "He is number one in the class."),
    ("hsk2_dong2",         "懂",   "dǒng",            "understand",
     "你懂我说的意思吗？",           "Nǐ dǒng wǒ shuō de yìsi ma?",             "Do you understand what I mean?"),
    ("hsk2_feichang",      "非常", "fēicháng",        "very / extremely",
     "这部电影非常精彩。",           "Zhè bù diànyǐng fēicháng jīngcǎi.",       "This film is extremely wonderful."),
    ("hsk2_guozhi",        "果汁", "guǒzhī",          "fruit juice",
     "我想喝一杯果汁。",             "Wǒ xiǎng hē yī bēi guǒzhī.",             "I would like a glass of fruit juice."),
    ("hsk2_hua",           "花",   "huā",             "flower / spend",
     "她送给我一束花。",             "Tā sòng gěi wǒ yī shù huā.",              "She gave me a bouquet of flowers."),
    ("hsk2_huai",          "坏",   "huài",            "bad / broken",
     "我的手机坏了。",               "Wǒ de shǒujī huài le.",                    "My phone is broken."),
    ("hsk2_huodong",       "活动", "huódòng",         "activity / event",
     "学校明天有文化活动。",         "Xuéxiào míngtiān yǒu wénhuà huódòng.",     "The school has a cultural event tomorrow."),
    ("hsk2_kaoshi",        "考试", "kǎoshì",          "exam / test",
     "下周我有一个重要的考试。",     "Xià zhōu wǒ yǒu yīgè zhòngyào de kǎoshì.", "I have an important exam next week."),
    ("hsk2_keneng",        "可能", "kěnéng",          "possible / maybe",
     "他可能今天不来了。",           "Tā kěnéng jīntiān bù lái le.",            "He may not come today."),
    ("hsk2_ke2",           "刻",   "kè",              "quarter hour",
     "现在是三点一刻。",             "Xiànzài shì sān diǎn yī kè.",             "It is now a quarter past three."),
    ("hsk2_ke3",           "课",   "kè",              "class / lesson",
     "我上午有三节课。",             "Wǒ shàngwǔ yǒu sān jié kè.",             "I have three classes in the morning."),
    ("hsk2_lishi",         "历史", "lìshǐ",           "history",
     "我很喜欢中国历史。",           "Wǒ hěn xǐhuān Zhōngguó lìshǐ.",           "I really like Chinese history."),
    ("hsk2_nan2",          "难",   "nán",             "difficult",
     "这道题太难了，我不会做。",     "Zhè dào tí tài nán le, wǒ bù huì zuò.",  "This question is too difficult; I can't do it."),
    ("hsk2_paobu",         "跑步", "pǎobù",           "run / jog",
     "我每天早上跑步半个小时。",     "Wǒ měitiān zǎoshàng pǎobù bàn gè xiǎoshí.", "I jog for half an hour every morning."),
    ("hsk2_pianyi",        "便宜", "piányí",          "cheap / inexpensive",
     "这家店的东西很便宜。",         "Zhè jiā diàn de dōngxi hěn piányí.",      "The things in this shop are very cheap."),
    ("hsk2_ranhou",        "然后", "ránhòu",          "then / afterwards",
     "先吃饭，然后去散步。",         "Xiān chīfàn, ránhòu qù sànbù.",           "Eat first, then go for a walk."),
    ("hsk2_renshi",        "认识", "rènshi",          "know (a person)",
     "很高兴认识你！",               "Hěn gāoxìng rènshi nǐ!",                  "Nice to meet you!"),
    ("hsk2_rongyi",        "容易", "róngyì",          "easy",
     "这道菜做起来很容易。",         "Zhè dào cài zuò qǐlái hěn róngyì.",       "This dish is very easy to make."),
    ("hsk2_shengbing",     "生病", "shēngbìng",       "get sick / be ill",
     "我昨天生病了，在家休息。",     "Wǒ zuótiān shēngbìng le, zài jiā xiūxi.", "I got sick yesterday and rested at home."),
    ("hsk2_shiqing",       "事情", "shìqíng",         "matter / thing",
     "有什么事情可以告诉我。",       "Yǒu shénme shìqíng kěyǐ gàosù wǒ.",      "You can tell me if there is anything."),
    ("hsk2_suiran",        "虽然", "suīrán",          "although / even though",
     "虽然很累，但他还是坚持学习。", "Suīrán hěn lèi, dàn tā háishi jiānchí xuéxí.", "Although tired, he still kept studying."),
    ("hsk2_ta3",           "它",   "tā",              "it",
     "这只猫很可爱，它叫小白。",     "Zhè zhī māo hěn kě'ài, tā jiào Xiǎo Bái.", "This cat is very cute; it is called Xiao Bai."),
    ("hsk2_tizuqiu",       "踢足球", "tī zúqiú",      "play soccer",
     "他们每周末一起踢足球。",       "Tāmen měi zhōumò yīqǐ tī zúqiú.",         "They play soccer together every weekend."),
    ("hsk2_tiaowu",        "跳舞", "tiàowǔ",          "dance",
     "她非常喜欢跳舞。",             "Tā fēicháng xǐhuān tiàowǔ.",              "She loves dancing very much."),
    ("hsk2_dadianhua",     "打电话", "dǎ diànhuà",    "make a phone call",
     "我给你打电话。",               "Wǒ gěi nǐ dǎ diànhuà.",                   "I'll give you a phone call."),
    ("hsk2_haochi",        "好吃", "hǎochī",          "delicious",
     "这道菜非常好吃！",             "Zhè dào cài fēicháng hǎochī!",             "This dish is extremely delicious!"),
    ("hsk2_pingguo",       "苹果", "píngguǒ",         "apple",
     "我每天吃一个苹果。",           "Wǒ měitiān chī yī gè píngguǒ.",           "I eat one apple every day."),
    ("hsk2_xigua",         "西瓜", "xīguā",           "watermelon",
     "夏天吃西瓜很解渴。",           "Xiàtiān chī xīguā hěn jiěkě.",             "Eating watermelon in summer is very refreshing."),
    ("hsk2_zuotian",       "昨天", "zuótiān",         "yesterday",
     "昨天我学了很多新词。",         "Zuótiān wǒ xué le hěn duō xīn cí.",       "Yesterday I learned many new words."),
]

# ---------------------------------------------------------------------------
# Stable IDs (generated once — must not change between runs)
# ---------------------------------------------------------------------------
MODEL_ID  = 1932067740
DECK_ID   = 1932067741

# ---------------------------------------------------------------------------
# Note model with 3 card templates
# ---------------------------------------------------------------------------
CSS = """
.card {
    font-family: Arial, "Noto Sans CJK SC", sans-serif;
    font-size: 20px;
    text-align: center;
    color: #222;
    background-color: #fafafa;
    padding: 20px;
}
.chinese { font-size: 48px; color: #fff; margin-bottom: 8px; }
.pinyin  { font-size: 22px; color: #555; margin-bottom: 4px; }
.english { font-size: 20px; color: #333; }
.sentence-zh { font-size: 28px; color: #333; margin: 12px 0 4px; }
.sentence-py { font-size: 16px; color: #666; }
.sentence-en { font-size: 16px; color: #888; }
hr { border: none; border-top: 1px solid #ddd; margin: 16px 0; }
"""

HSK2_MODEL = genanki.Model(
    MODEL_ID,
    "HSK 2 Vocabulary",
    fields=[
        {"name": "VocabId"},
        {"name": "Chinese"},
        {"name": "Pinyin"},
        {"name": "English"},
        {"name": "Sentence"},
        {"name": "SentencePinyin"},
        {"name": "SentenceEnglish"},
        {"name": "Audio"},        # [sound:hsk2_xxx.mp3] or empty
    ],
    templates=[
        # ── Card 1: Word Recognition ─────────────────────────────────────
        {
            "name": "Word",
            "qfmt": '<div class="chinese">{{Chinese}}</div>',
            "afmt": """\
{{FrontSide}}
<hr>
<div class="pinyin">{{Pinyin}}</div>
<div class="english">{{English}}</div>
<br>
<div class="sentence-zh">{{Sentence}}</div>
<div class="sentence-py">{{SentencePinyin}}</div>
<div class="sentence-en">{{SentenceEnglish}}</div>
{{Audio}}
""",
        },
        # ── Card 2: Sentence Reading ─────────────────────────────────────
        {
            "name": "Sentence",
            "qfmt": """\
<div class="sentence-zh">{{Sentence}}</div>
{{Audio}}
""",
            "afmt": """\
{{FrontSide}}
<hr>
<div class="sentence-py">{{SentencePinyin}}</div>
<div class="sentence-en">{{SentenceEnglish}}</div>
<br>
<div class="chinese">{{Chinese}}</div>
<div class="pinyin">{{Pinyin}}</div>
<div class="english">{{English}}</div>
{{Audio}}
""",
        },
        # ── Card 3: Audio Listening ──────────────────────────────────────
        {
            "name": "Audio",
            "qfmt": """\
{{#Audio}}
<div style="font-size:64px">🔊</div>
{{Audio}}
<div style="color:#aaa; font-size:14px">What is the sentence and word?</div>
{{/Audio}}
{{^Audio}}
[no audio for this card]
{{/Audio}}
""",
            "afmt": """\
{{FrontSide}}
<hr>
<div class="sentence-zh">{{Sentence}}</div>
<div class="sentence-py">{{SentencePinyin}}</div>
<div class="sentence-en">{{SentenceEnglish}}</div>
<br>
<div class="chinese">{{Chinese}}</div>
<div class="pinyin">{{Pinyin}}</div>
<div class="english">{{English}}</div>
""",
        },
    ],
    css=CSS,
)


def make_note(vocab_id, chinese, pinyin, english, sentence, sent_py, sent_en,
              audio_tag):
    """Return a genanki.Note for one vocabulary item."""
    return genanki.Note(
        model=HSK2_MODEL,
        fields=[
            vocab_id,
            chinese,
            pinyin,
            english,
            sentence,
            sent_py,
            sent_en,
            audio_tag,
        ],
        # Stable GUID derived from the vocab id so re-runs update existing notes
        guid=genanki.guid_for(vocab_id),
    )


def build_deck(output_path: str) -> None:
    deck = genanki.Deck(DECK_ID, "HSK 2 Vocabulary")
    media_files = []

    missing_audio = []

    for entry in HSK2_VOCAB:
        vocab_id, chinese, pinyin, english, sentence, sent_py, sent_en = entry
        mp3_name = f"{vocab_id}.mp3"
        mp3_path = os.path.join(AUDIO_DIR, mp3_name)

        if os.path.isfile(mp3_path):
            audio_tag = f"[sound:{mp3_name}]"
            media_files.append(mp3_path)
        else:
            audio_tag = ""
            missing_audio.append(vocab_id)

        note = make_note(vocab_id, chinese, pinyin, english,
                         sentence, sent_py, sent_en, audio_tag)
        deck.add_note(note)

    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file(output_path)

    total = len(HSK2_VOCAB)
    with_audio = total - len(missing_audio)
    print(f"Created {output_path}")
    print(f"  {total} vocabulary entries → {total * 3} cards "
          f"(3 per entry: Word / Sentence / Audio)")
    print(f"  Audio files embedded: {with_audio}/{total}")
    if missing_audio:
        print(f"  Missing audio ({len(missing_audio)}): "
              + ", ".join(missing_audio))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    default_output = os.path.join(SCRIPT_DIR, "hsk2.apkg")
    parser.add_argument("--output", "-o", default=default_output,
                        help=f"Output .apkg path (default: {default_output})")
    args = parser.parse_args()
    build_deck(args.output)


if __name__ == "__main__":
    main()
