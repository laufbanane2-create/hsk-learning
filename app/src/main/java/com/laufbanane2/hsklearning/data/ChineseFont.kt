package com.laufbanane2.hsklearning.data

import android.content.SharedPreferences

data class ChineseFont(
    val key: String,
    val displayName: String,
    val googleQuery: String,
    val enabledByDefault: Boolean = true
)

object ChineseFonts {
    val ALL = listOf(
        ChineseFont("font_noto_sans_sc",          "Noto Sans SC",          "Noto Sans SC",          enabledByDefault = true),
        ChineseFont("font_noto_serif_sc",         "Noto Serif SC",         "Noto Serif SC",         enabledByDefault = true),
        ChineseFont("font_zcool_xiaowei",         "ZCOOL XiaoWei",         "ZCOOL XiaoWei",         enabledByDefault = true),
        ChineseFont("font_ma_shan_zheng",         "Ma Shan Zheng",         "Ma Shan Zheng",         enabledByDefault = true),
        ChineseFont("font_zcool_qingke_huangyou", "ZCOOL QingKe HuangYou", "ZCOOL QingKe HuangYou", enabledByDefault = true),
        ChineseFont("font_liu_jian_mao_cao",      "Liu Jian Mao Cao",      "Liu Jian Mao Cao",      enabledByDefault = false)
    )

    fun isEnabled(prefs: SharedPreferences, font: ChineseFont): Boolean =
        prefs.getBoolean(font.key, font.enabledByDefault)
}
