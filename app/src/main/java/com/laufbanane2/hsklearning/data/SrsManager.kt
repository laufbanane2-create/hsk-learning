package com.laufbanane2.hsklearning.data

import android.content.Context

/**
 * Spaced-repetition scheduler (SM-2 inspired).
 *
 * Each vocabulary card tracks:
 *  - intervalMs   – current review interval in milliseconds
 *  - nextReviewMs – epoch-ms timestamp when the card is next due
 *  - repetitions  – consecutive correct answers
 *  - easeFactor   – multiplier applied to the interval on a correct answer
 *
 * Correct answer → interval grows (× easeFactor), ease increases slightly.
 * Wrong answer   → interval resets to 1 minute, ease decreases slightly.
 */
class SrsManager(context: Context) {

    private val prefs = context.getSharedPreferences("srs_data", Context.MODE_PRIVATE)

    companion object {
        private const val DEFAULT_EASE = 2.5f
        private const val MIN_EASE = 1.3f
        private const val MAX_EASE = 5.0f
        private const val MIN_INTERVAL_MS = 60_000L          // 1 minute
        private const val FIRST_CORRECT_MS = 60_000L         // 1 minute
        private const val SECOND_CORRECT_MS = 600_000L       // 10 minutes
    }

    // ── Public queries ────────────────────────────────────────────────────────

    fun getIntervalMs(vocabId: String): Long =
        prefs.getLong("${vocabId}_interval", 0L)

    fun getNextReviewMs(vocabId: String): Long =
        prefs.getLong("${vocabId}_next_review", 0L)

    /** True when the card has never been answered or its due timestamp has passed. */
    fun isDue(vocabId: String): Boolean =
        getNextReviewMs(vocabId) <= System.currentTimeMillis()

    /**
     * Returns the earliest future due-timestamp among [vocabIds],
     * or null if every card is already due.
     */
    fun nextDueAfterNow(vocabIds: List<String>): Long? {
        val now = System.currentTimeMillis()
        return vocabIds.map { getNextReviewMs(it) }.filter { it > now }.minOrNull()
    }

    // ── Answer recording ──────────────────────────────────────────────────────

    fun recordAnswer(vocabId: String, correct: Boolean) {
        val now = System.currentTimeMillis()
        val intervalMs = getIntervalMs(vocabId)
        val reps = prefs.getInt("${vocabId}_reps", 0)
        val ease = prefs.getFloat("${vocabId}_ease", DEFAULT_EASE)

        val newIntervalMs: Long
        val newReps: Int
        val newEase: Float

        if (correct) {
            newReps = reps + 1
            newEase = (ease + 0.1f).coerceAtMost(MAX_EASE)
            newIntervalMs = when (reps) {
                0 -> FIRST_CORRECT_MS
                1 -> SECOND_CORRECT_MS
                else -> (intervalMs * ease).toLong().coerceAtLeast(MIN_INTERVAL_MS)
            }
        } else {
            newReps = 0
            newEase = (ease - 0.2f).coerceAtLeast(MIN_EASE)
            newIntervalMs = MIN_INTERVAL_MS
        }

        prefs.edit()
            .putLong("${vocabId}_interval", newIntervalMs)
            .putLong("${vocabId}_next_review", now + newIntervalMs)
            .putInt("${vocabId}_reps", newReps)
            .putFloat("${vocabId}_ease", newEase)
            .apply()
    }

    // ── Formatting helpers ────────────────────────────────────────────────────

    /** Human-readable interval for a card (e.g. "New", "5m", "2h 10m", "3d 4h"). */
    fun formatInterval(vocabId: String): String {
        val ms = getIntervalMs(vocabId)
        return if (ms == 0L) "New" else formatMs(ms)
    }

    /** Human-readable time until the card is next due (e.g. "Due now", "in 1h 30m"). */
    fun formatNextReview(vocabId: String): String {
        val nextMs = getNextReviewMs(vocabId)
        if (nextMs == 0L) return "New"
        val diffMs = nextMs - System.currentTimeMillis()
        return if (diffMs <= 0) "Due now" else "in ${formatMs(diffMs)}"
    }

    fun formatMs(ms: Long): String {
        val minutes = ms / 60_000
        val hours = minutes / 60
        val days = hours / 24
        return when {
            days > 0 -> "${days}d ${hours % 24}h"
            hours > 0 -> "${hours}h ${minutes % 60}m"
            minutes > 0 -> "${minutes}m"
            else -> "<1m"
        }
    }
}
