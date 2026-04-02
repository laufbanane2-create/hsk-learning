package com.laufbanane2.hsklearning.data

data class VocabItem(
    val id: String,
    val level: Int,
    val chinese: String,
    val pinyin: String,
    val english: String,
    val sentence: String,
    val sentencePinyin: String,
    val sentenceEnglish: String
)
