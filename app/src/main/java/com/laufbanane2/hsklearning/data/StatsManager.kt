package com.laufbanane2.hsklearning.data

import android.content.Context

class StatsManager(context: Context) {

    private val prefs = context.getSharedPreferences("vocab_stats", Context.MODE_PRIVATE)

    fun getCorrect(vocabId: String): Int = prefs.getInt("${vocabId}_correct", 0)

    fun getWrong(vocabId: String): Int = prefs.getInt("${vocabId}_wrong", 0)

    fun incrementCorrect(vocabId: String) {
        val current = getCorrect(vocabId)
        prefs.edit().putInt("${vocabId}_correct", current + 1).apply()
    }

    fun incrementWrong(vocabId: String) {
        val current = getWrong(vocabId)
        prefs.edit().putInt("${vocabId}_wrong", current + 1).apply()
    }
}
