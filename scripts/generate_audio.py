#!/usr/bin/env python3
"""
Build-time audio generation script for HSK Learning.

Generates MP3 files for every vocabulary sentence using the ElevenLabs API
(model: eleven_v3, voice: Bella) and writes them to
audio/ at the repository root.

Usage:
    python3 scripts/generate_audio.py --api-key <ELEVENLABS_API_KEY>

    Or set the ELEVENLABS_API_KEY environment variable and run without --api-key.

The script is idempotent: files that already exist are skipped unless
--force is passed.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

# ---------------------------------------------------------------------------
# Vocabulary data — mirrors VocabData.kt so the script has no build dependency
# on the Android project.  Keep in sync with VocabData.kt.
# ---------------------------------------------------------------------------
VOCAB = [
    # HSK 1
    ("hsk1_ai",       "我爱我的家人。"),
    ("hsk1_ba",       "我爸爸在家工作。"),
    ("hsk1_beizi",    "请给我一个杯子。"),
    ("hsk1_bu",       "我不喝咖啡，我喝茶。"),
    ("hsk1_chi",      "我喜欢吃米饭。"),
    ("hsk1_da",       "这个苹果很大。"),
    ("hsk1_dianshi",  "我每天晚上看电视。"),
    ("hsk1_diannao",  "他用电脑工作。"),
    ("hsk1_gou",      "我家有一只狗。"),
    ("hsk1_hao",      "今天天气很好。"),
    ("hsk1_he",       "我想喝一杯茶。"),
    ("hsk1_hen",      "我今天很高兴。"),
    ("hsk1_hui",      "我会说一点汉语。"),
    ("hsk1_jia",      "我家在北京附近。"),
    ("hsk1_jintian",  "今天是星期几？"),
    ("hsk1_kan",      "我们一起看书吧。"),
    ("hsk1_lai",      "请你来我家吃饭。"),
    ("hsk1_laoshi",   "我的老师很好。"),
    ("hsk1_mama",     "我妈妈在家做饭。"),
    ("hsk1_mao",      "我有一只猫。"),
    ("hsk1_meiyou",   "我今天没有时间。"),
    ("hsk1_mingtian", "明天我去学校。"),
    ("hsk1_nihao",    "你好，我叫小明。"),
    ("hsk1_pengyou",  "他是我的好朋友。"),
    ("hsk1_qu",       "我们去北京旅游。"),
    ("hsk1_shi",      "我是学生。"),
    ("hsk1_shu",      "这本书很有意思。"),
    ("hsk1_shui",     "请给我一杯水。"),
    ("hsk1_xuesheng", "他们都是学生。"),
    ("hsk1_you",      "你有兄弟姐妹吗？"),
    ("hsk1_zai",      "他在哪里工作？"),
    ("hsk1_zaijian",  "明天见，再见！"),
    ("hsk1_zhongguo", "我来自中国。"),
    ("hsk1_xuexi",    "我每天学习汉语。"),
    ("hsk1_tianqi",   "今天天气怎么样？"),
    ("hsk1_ba2",        "我有八本书。"),
    ("hsk1_beijing",    "北京是中国的首都。"),
    ("hsk1_bukeqi",     "谢谢你！不客气。"),
    ("hsk1_cai",        "这道菜很好吃。"),
    ("hsk1_cha",        "我每天喝茶。"),
    ("hsk1_chuzuche",   "我坐出租车去机场。"),
    ("hsk1_de",         "这是我的书。"),
    ("hsk1_dongxi",     "你买了什么东西？"),
    ("hsk1_dou",        "我们都是学生。"),
    ("hsk1_duibuqi",    "对不起，我来晚了。"),
    ("hsk1_duo",        "这里有很多人。"),
    ("hsk1_duoshao",    "这个多少钱？"),
    ("hsk1_e",          "我饿了，我们去吃饭吧。"),
    ("hsk1_er",         "我有两个哥哥。"),
    ("hsk1_feiji",      "我坐飞机去上海。"),
    ("hsk1_fenzhong",   "请等我五分钟。"),
    ("hsk1_gaoxing",    "见到你我很高兴。"),
    ("hsk1_ge",         "请给我一个苹果。"),
    ("hsk1_gongzuo",    "他在银行工作。"),
    ("hsk1_hanyu",      "我在学习汉语。"),
    ("hsk1_hao2",       "今天几号？"),
    ("hsk1_he2",        "我和你是朋友。"),
    ("hsk1_houmian",    "他在我后面。"),
    ("hsk1_hui2",       "我下午回家。"),
    ("hsk1_ji",         "你有几个朋友？"),
    ("hsk1_jiao",       "我叫小明。"),
    ("hsk1_jiu",        "一个月有三十天，我工作了九天。"),
    ("hsk1_kai",        "请开门。"),
    ("hsk1_kanjian",    "我看见他了。"),
    ("hsk1_kuai",       "这个苹果一块钱。"),
    ("hsk1_le",         "我吃了早饭。"),
    ("hsk1_li",         "书包里有很多书。"),
    ("hsk1_liang",      "请给我两杯茶。"),
    ("hsk1_ling",       "今天气温是零度。"),
    ("hsk1_liu",        "一个星期有七天，我上了六天课。"),
    ("hsk1_lu",         "这条路很长。"),
    ("hsk1_ma",         "你喜欢吃饺子吗？"),
    ("hsk1_meiguanxi",  "没关系，不要担心。"),
    ("hsk1_meimei",     "我妹妹很可爱。"),
    ("hsk1_men",        "同学们，我们开始上课吧。"),
    ("hsk1_mingzi",     "你的名字叫什么？"),
    ("hsk1_na",         "你喜欢哪个颜色？"),
    ("hsk1_nar",        "你要去哪儿？"),
    ("hsk1_na2",        "那是我的书。"),
    ("hsk1_ne",         "我很好，你呢？"),
    ("hsk1_ni",         "你好！你叫什么名字？"),
    ("hsk1_nian",       "今年我二十岁。"),
    ("hsk1_nuer",       "他有一个可爱的女儿。"),
    ("hsk1_nuren",      "那位女人是我的老师。"),
    ("hsk1_piaoliang",  "这朵花很漂亮。"),
    ("hsk1_qi",         "一个星期有七天。"),
    ("hsk1_qian",       "你有多少钱？"),
    ("hsk1_qianmian",   "学校就在前面。"),
    ("hsk1_qing",       "请坐！"),
    ("hsk1_re",         "今天天气很热。"),
    ("hsk1_ren",        "这里有很多人。"),
    ("hsk1_ri",         "今天是几月几日？"),
    ("hsk1_san",        "我家有三口人。"),
    ("hsk1_shangdian",  "商店几点开门？"),
    ("hsk1_shang",      "书在桌子上。"),
    ("hsk1_shangwu",    "我上午去学校上课。"),
    ("hsk1_shao",       "这里人很少，很安静。"),
    ("hsk1_shei",       "那个人是谁？"),
    ("hsk1_shenme",     "你想吃什么？"),
    ("hsk1_shengri",    "今天是我的生日！"),
    ("hsk1_shihou",     "你什么时候来我家？"),
    ("hsk1_si",         "一年有四个季节。"),
    ("hsk1_sui",        "他今年二十五岁了。"),
    ("hsk1_shuijiao",   "我每天晚上十一点睡觉。"),
    ("hsk1_shuiguo",    "我每天吃水果，对身体好。"),
    ("hsk1_shuo",       "请说慢一点儿。"),
    ("hsk1_ta",         "他是我的老师。"),
    ("hsk1_ta2",        "她是我的好朋友。"),
    ("hsk1_tai",        "这个太贵了，我买不起。"),
    ("hsk1_ting",       "我喜欢听音乐。"),
    ("hsk1_tongxue",    "他是我的同学。"),
    ("hsk1_wei",        "喂，你好，请问李老师在吗？"),
    ("hsk1_wo",         "我是一名学生。"),
    ("hsk1_women",      "我们一起去图书馆吧。"),
    ("hsk1_wu",         "我有五本中文书。"),
    ("hsk1_xia",        "猫在桌子下面。"),
    ("hsk1_xiawu",      "下午我去图书馆看书。"),
    ("hsk1_xiayu",      "今天下雨了，记得带伞。"),
    ("hsk1_xiansheng",  "王先生，您好！"),
    ("hsk1_xianzai",    "现在几点了？"),
    ("hsk1_xiang",      "我想回家休息。"),
    ("hsk1_xiao",       "这个房间很小，只有一张床。"),
    ("hsk1_xiaojie",    "请问，小姐，洗手间在哪里？"),
    ("hsk1_xie",        "我买了一些水果和蔬菜。"),
    ("hsk1_xiexie",     "谢谢你的帮助！"),
    ("hsk1_xingqi",     "这个星期我有很多作业。"),
    ("hsk1_yi",         "我只有一个苹果。"),
    ("hsk1_yidianr",    "我会说一点儿汉语。"),
    ("hsk1_yifu",       "我要买一些新衣服。"),
    ("hsk1_yisheng",    "我头疼，要去看医生。"),
    ("hsk1_yiyuan",     "医院在学校旁边。"),
    ("hsk1_yizi",       "请坐在椅子上等一下。"),
    ("hsk1_yinwei",     "我喜欢汉语，因为它很有趣。"),
    ("hsk1_yue",        "一年有十二个月。"),
    ("hsk1_zenme",      "这个字怎么写？"),
    ("hsk1_zenmeyang",  "你觉得这个菜怎么样？"),
    ("hsk1_zhe",        "这是什么？"),
    ("hsk1_zhongwu",    "中午我们一起去吃饭吧。"),
    ("hsk1_zhu",        "你住在哪里？"),
    ("hsk1_zhuozi",     "书放在桌子上。"),
    ("hsk1_ben",        "我买了三本书。"),
    ("hsk1_dian",       "现在是三点。"),
    ("hsk1_dianying",   "我周末喜欢看电影。"),
    ("hsk1_erzi",       "他有一个聪明的儿子。"),
    ("hsk1_zi",         "这个字怎么写？"),
    ("hsk1_dadianhua",  "我给妈妈打电话。"),
    ("hsk1_pingguo",    "我每天吃一个苹果。"),
    ("hsk1_xigua",      "夏天吃西瓜很解渴。"),
    ("hsk1_zuotian",    "昨天我见了一个老朋友。"),
    ("hsk1_haochi",     "这道菜非常好吃！"),
    # HSK 2
    ("hsk2_bangzhu",   "谢谢你帮助我。"),
    ("hsk2_bi",        "今天比昨天冷。"),
    ("hsk2_bie",       "别忘了带水。"),
    ("hsk2_chuan",     "今天很冷，多穿衣服。"),
    ("hsk2_cong",      "我从北京来。"),
    ("hsk2_danshi",    "我想去，但是没有时间。"),
    ("hsk2_difang",    "北京是一个好地方。"),
    ("hsk2_du",        "他喜欢读书。"),
    ("hsk2_dui",       "你说的对。"),
    ("hsk2_fangjian",  "我的房间很小。"),
    ("hsk2_gaosu",     "请告诉我你的名字。"),
    ("hsk2_gen",       "我跟朋友一起去。"),
    ("hsk2_hai",       "他还在学校。"),
    ("hsk2_haizi",     "这个孩子很聪明。"),
    ("hsk2_huanying",  "欢迎来到我家。"),
    ("hsk2_huozhe",    "你喝茶或者咖啡？"),
    ("hsk2_jichang",   "我去机场接朋友。"),
    ("hsk2_jide",      "你记得我的名字吗？"),
    ("hsk2_juede",     "我觉得今天很冷。"),
    ("hsk2_kaishi",    "我们开始学习吧。"),
    ("hsk2_li",        "学校离我家很近。"),
    ("hsk2_lianxi",    "每天练习说汉语。"),
    ("hsk2_luyou",     "我喜欢旅游，看新地方。"),
    ("hsk2_nan",       "汉语有一点难。"),
    ("hsk2_piao",      "我买了两张电影票。"),
    ("hsk2_ren",       "我认识她，她是我朋友。"),
    ("hsk2_shenti",    "身体健康最重要。"),
    ("hsk2_shijian",   "我没有时间看电视。"),
    ("hsk2_xihuan",    "我喜欢学习汉语。"),
    ("hsk2_xiao",      "他总是笑着说话。"),
    ("hsk2_yiqi",      "我们一起去吃饭吧。"),
    ("hsk2_zhunbei",   "我在准备考试。"),
    ("hsk2_zuo",       "我坐公共汽车去学校。"),
    ("hsk2_ayi",             "我的阿姨住在上海。"),
    ("hsk2_ba",              "我们去看电影吧。"),
    ("hsk2_ban",             "现在是七点半。"),
    ("hsk2_banfa",           "我没有办法去。"),
    ("hsk2_bang",            "请帮我拿一下包。"),
    ("hsk2_bieren",          "不要总是担心别人怎么看你。"),
    ("hsk2_binguan",         "我住在一家宾馆里。"),
    ("hsk2_bingxiang",       "牛奶在冰箱里。"),
    ("hsk2_cai2",            "他才来了。"),
    ("hsk2_cha2",            "我的汉语还差得很远。"),
    ("hsk2_chang",           "这条路很长，要走很久。"),
    ("hsk2_changge",         "她很喜欢唱歌。"),
    ("hsk2_chaoshi",         "我去超市买水果和蔬菜。"),
    ("hsk2_chulai",          "请你出来一下。"),
    ("hsk2_da2",             "他喜欢打篮球。"),
    ("hsk2_dasuan",          "你打算去哪里旅游？"),
    ("hsk2_dangran",         "当然，我很乐意帮你。"),
    ("hsk2_ditie",           "我每天坐地铁去上班。"),
    ("hsk2_dong",            "请不要动，我帮你拍照。"),
    ("hsk2_fa",              "我给你发一条消息。"),
    ("hsk2_fangbian",        "住在学校附近很方便。"),
    ("hsk2_fang",            "请把书放在桌子上。"),
    ("hsk2_fen",             "我们还有十分钟。"),
    ("hsk2_fuwuyuan",        "服务员，请给我一杯水。"),
    ("hsk2_gei",             "妈妈给我买了一个礼物。"),
    ("hsk2_geng",            "今天比昨天更冷。"),
    ("hsk2_gonggongqiche",   "我坐公共汽车去学校。"),
    ("hsk2_gongsi",          "他在一家大公司工作。"),
    ("hsk2_gushi",           "妈妈每天晚上给我讲故事。"),
    ("hsk2_guanxi",          "我们的关系很好。"),
    ("hsk2_gui",             "这件衣服很贵，我买不起。"),
    ("hsk2_hei",             "他有一只黑猫。"),
    ("hsk2_houlai",          "他先工作，后来去吃饭。"),
    ("hsk2_huilai",          "他出去了，等一下就回来。"),
    ("hsk2_haishi",          "你喝茶还是咖啡？"),
    ("hsk2_jiandan",         "这道题很简单。"),
    ("hsk2_jian",            "我买了两件衣服。"),
    ("hsk2_keyi",            "我可以问你一个问题吗？"),
    ("hsk2_liaotian",        "我们在咖啡馆聊天。"),
    ("hsk2_mai",             "这家店卖新鲜水果。"),
    ("hsk2_mianbao",         "我早上吃面包和鸡蛋。"),
    ("hsk2_miantiao",        "我最喜欢吃面条。"),
    ("hsk2_mingbai",         "你明白我的意思吗？"),
    ("hsk2_name",            "那么，我们明天见吧。"),
    ("hsk2_neng",            "你能帮我吗？"),
    ("hsk2_pang",            "他觉得自己有点胖，想减肥。"),
    ("hsk2_putonghua",       "在中国，人们说普通话。"),
    ("hsk2_qishi",           "其实，他是一个很好的人。"),
    ("hsk2_qi",              "我骑自行车去学校。"),
    ("hsk2_rang",            "请让我先说。"),
    ("hsk2_ruguo",           "如果明天下雨，我就不去了。"),
    ("hsk2_shengqi",         "别生气，这件事不重要。"),
    ("hsk2_shouji",          "我的手机没有电了。"),
    ("hsk2_song",            "他送给我一本书。"),
    ("hsk2_suoyi",           "天气很冷，所以我穿了厚衣服。"),
    ("hsk2_tebie",           "这家餐厅的菜特别好吃。"),
    ("hsk2_tian",            "这个蛋糕很甜。"),
    ("hsk2_tingshu",         "听说他要去北京工作。"),
    ("hsk2_tongshi",         "他是我的同事，我们一起工作。"),
    ("hsk2_toufa",           "她有一头漂亮的长头发。"),
    ("hsk2_weishenme",       "你为什么学习汉语？"),
    ("hsk2_wenhua",          "中国文化非常丰富。"),
    ("hsk2_wen",             "我可以问你一个问题吗？"),
    ("hsk2_wenti",           "这道题有问题，我不会做。"),
    ("hsk2_xi",              "我每天早上洗脸。"),
    ("hsk2_xiaoshi",         "我每天学习两个小时汉语。"),
    ("hsk2_xie",             "请你写一下你的名字。"),
    ("hsk2_xinglixiang",     "我的行李箱太重了。"),
    ("hsk2_yihou",           "以后我想去中国旅游。"),
    ("hsk2_yiqian",          "以前我不喜欢吃蔬菜。"),
    ("hsk2_yijing",          "他已经回家了。"),
    ("hsk2_yong",            "你用什么语言说话？"),
    ("hsk2_youming",         "这家餐厅很有名。"),
    ("hsk2_zai2",            "请再说一遍。"),
    ("hsk2_zhang",           "我买了两张电影票。"),
    ("hsk2_zhao",            "我在找我的钥匙。"),
    ("hsk2_zhen",            "这个故事是真的吗？"),
    ("hsk2_zhengzai",        "他正在学习汉语。"),
    ("hsk2_zhidao",          "你知道他住在哪里吗？"),
    ("hsk2_zhi",             "我只喝水，不喝咖啡。"),
    ("hsk2_zhongyao",        "健康比金钱更重要。"),
    ("hsk2_shuohua",         "上课的时候不要说话。"),
    ("hsk2_man",             "请说慢一点，我听不清楚。"),
    ("hsk2_kuai2",           "他走路很快。"),
    ("hsk2_xin",             "我买了一本新书。"),
    ("hsk2_leng",            "今天很冷，多穿衣服。"),
    ("hsk2_bai",             "她穿了一件白衬衫。"),
    ("hsk2_bai2",            "这本书一百页。"),
    ("hsk2_baozhi",          "我爸爸每天早上看报纸。"),
    ("hsk2_ci",              "我去过北京两次。"),
    ("hsk2_cuo",             "对不起，我说错了。"),
    ("hsk2_dajia",           "大家好，我叫李明。"),
    ("hsk2_ditu",            "请给我看一下地图。"),
    ("hsk2_diyi",            "他是班里第一名。"),
    ("hsk2_dong2",           "你懂我说的意思吗？"),
    ("hsk2_feichang",        "这部电影非常精彩。"),
    ("hsk2_guozhi",          "我想喝一杯果汁。"),
    ("hsk2_hua",             "她送给我一束花。"),
    ("hsk2_huai",            "我的手机坏了。"),
    ("hsk2_huodong",         "学校明天有文化活动。"),
    ("hsk2_kaoshi",          "下周我有一个重要的考试。"),
    ("hsk2_keneng",          "他可能今天不来了。"),
    ("hsk2_ke2",             "现在是三点一刻。"),
    ("hsk2_ke3",             "我上午有三节课。"),
    ("hsk2_lishi",           "我很喜欢中国历史。"),
    ("hsk2_nan2",            "这道题太难了，我不会做。"),
    ("hsk2_paobu",           "我每天早上跑步半个小时。"),
    ("hsk2_pianyi",          "这家店的东西很便宜。"),
    ("hsk2_ranhou",          "先吃饭，然后去散步。"),
    ("hsk2_renshi",          "很高兴认识你！"),
    ("hsk2_rongyi",          "这道菜做起来很容易。"),
    ("hsk2_shengbing",       "我昨天生病了，在家休息。"),
    ("hsk2_shiqing",         "有什么事情可以告诉我。"),
    ("hsk2_suiran",          "虽然很累，但他还是坚持学习。"),
    ("hsk2_ta3",             "这只猫很可爱，它叫小白。"),
    ("hsk2_tizuqiu",         "他们每周末一起踢足球。"),
    ("hsk2_tiaowu",          "她非常喜欢跳舞。"),
]

VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Bella
MODEL_ID = "eleven_v3"
API_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

# Seconds to wait between requests to respect rate limits.
REQUEST_DELAY = 0.5


def generate_mp3(text: str, api_key: str) -> bytes:
    payload = json.dumps({
        "text": text,
        "model_id": MODEL_ID,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
        },
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "xi-api-key": api_key,
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate bundled audio assets via ElevenLabs.")
    parser.add_argument("--api-key", default=os.environ.get("ELEVENLABS_API_KEY", ""),
                        help="ElevenLabs API key (or set ELEVENLABS_API_KEY env var)")
    parser.add_argument("--force", action="store_true",
                        help="Re-generate even if the MP3 already exists")
    parser.add_argument("--output-dir", default=None,
                        help="Directory to write MP3 files (default: audio/ at repo root)")
    args = parser.parse_args()

    api_key = args.api_key.strip()
    if not api_key:
        print("ERROR: No API key provided. Use --api-key or set ELEVENLABS_API_KEY.", file=sys.stderr)
        sys.exit(1)

    # Resolve output directory relative to the project root (one level up from
    # this script's own directory when the script lives in scripts/).
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    output_dir = args.output_dir or os.path.join(project_root, "audio")
    os.makedirs(output_dir, exist_ok=True)

    total = len(VOCAB)
    generated = 0
    skipped = 0
    failed = 0

    for idx, (vocab_id, sentence) in enumerate(VOCAB, start=1):
        out_path = os.path.join(output_dir, f"{vocab_id}.mp3")
        if os.path.exists(out_path) and not args.force:
            print(f"[{idx}/{total}] SKIP  {vocab_id} (already exists)")
            skipped += 1
            continue

        print(f"[{idx}/{total}] GEN   {vocab_id}: {sentence}")
        try:
            audio_bytes = generate_mp3(sentence, api_key)
            with open(out_path, "wb") as f:
                f.write(audio_bytes)
            generated += 1
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")
            print(f"        ERROR HTTP {exc.code}: {body}", file=sys.stderr)
            failed += 1
        except urllib.error.URLError as exc:
            print(f"        ERROR network: {exc.reason}", file=sys.stderr)
            failed += 1
        except OSError as exc:
            print(f"        ERROR writing file: {exc}", file=sys.stderr)
            failed += 1

        # Brief pause to avoid hitting rate limits.
        if idx < total:
            time.sleep(REQUEST_DELAY)

    print(f"\nDone. generated={generated}, skipped={skipped}, failed={failed}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
