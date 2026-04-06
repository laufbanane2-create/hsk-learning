package com.laufbanane2.hsklearning.data

import android.content.Context

/**
 * Spaced-repetition scheduler (SM-2 inspired).
 *
 * Each vocabulary card has three independently-scheduled aspects:
 *  - READING        – recognise the Chinese word (no audio)
 *  - LISTENING      – translate the spoken sentence (audio only)
 *  - READING_SENTENCE – translate the written Chinese sentence (no pinyin)
 *
 * Each aspect tracks its own interval, nextReview, repetitions, and ease.
 * A card graduates (ACTIVE → GRADUATED) only once ALL three aspects have
 * been mastered ([GRADUATION_THRESHOLD] consecutive correct answers each).
 *
 * Correct answer → interval grows (× easeFactor), ease increases slightly.
 * Wrong answer   → interval resets to 1 minute, ease decreases slightly.
 *
 * Active/passive deck:
 *  Only ACTIVE cards are shown during normal study. A card is promoted from
 *  NEW to ACTIVE when an empty slot in the active deck is available.
 *  The deck stays full by immediately promoting the next NEW card after a
 *  graduation.
 */
class SrsManager(context: Context) {

    private val prefs = context.getSharedPreferences("srs_data", Context.MODE_PRIVATE)

    enum class CardStatus { NEW, ACTIVE, GRADUATED }

    /** The three independently-tracked study aspects for every vocabulary card. */
    enum class AspectType(val key: String) {
        READING("reading"),
        LISTENING("listening"),
        READING_SENTENCE("reading_sentence")
    }

    companion object {
        private const val DEFAULT_EASE = 2.5f
        private const val MIN_EASE = 1.3f
        private const val MAX_EASE = 5.0f
        private const val MIN_INTERVAL_MS = 60_000L          // 1 minute
        private const val FIRST_CORRECT_MS = 60_000L         // 1 minute
        private const val SECOND_CORRECT_MS = 600_000L       // 10 minutes
        /** Consecutive correct answers required to graduate one aspect. */
        const val GRADUATION_THRESHOLD = 3
        val ALL_ASPECTS: List<AspectType> = AspectType.values().toList()
    }

    // ── Card status ───────────────────────────────────────────────────────────

    fun getCardStatus(vocabId: String): CardStatus =
        when (prefs.getString("${vocabId}_status", "new")) {
            "active"    -> CardStatus.ACTIVE
            "graduated" -> CardStatus.GRADUATED
            else        -> CardStatus.NEW
        }

    private fun setCardStatus(vocabId: String, status: CardStatus) {
        prefs.edit().putString("${vocabId}_status", status.name.lowercase()).apply()
    }

    /** Returns all IDs from [allIds] whose status is [CardStatus.ACTIVE]. */
    fun getActiveIds(allIds: List<String>): List<String> =
        allIds.filter { getCardStatus(it) == CardStatus.ACTIVE }

    /**
     * Ensures the active deck has exactly [deckSize] cards.
     * - If there are fewer ACTIVE cards than [deckSize], promotes NEW cards to fill slots.
     * - If there are more ACTIVE cards than [deckSize] (e.g. the user lowered the setting),
     *   demotes the excess back to NEW, preferring cards with the least study progress.
     * GRADUATED cards are never touched.
     */
    fun initializeActiveDeck(allIds: List<String>, deckSize: Int) {
        val activeIds = allIds.filter { getCardStatus(it) == CardStatus.ACTIVE }
        val currentActiveCount = activeIds.size

        if (currentActiveCount > deckSize) {
            // Demote excess cards; prefer those with the least total reps (least studied).
            val excess = currentActiveCount - deckSize
            activeIds
                .sortedBy { id -> ALL_ASPECTS.sumOf { aspect -> prefs.getInt(repsKey(id, aspect), 0) } }
                .take(excess)
                .forEach { setCardStatus(it, CardStatus.NEW) }
        } else {
            val slotsToFill = deckSize - currentActiveCount
            if (slotsToFill > 0) {
                allIds
                    .filter { getCardStatus(it) == CardStatus.NEW }
                    .take(slotsToFill)
                    .forEach { setCardStatus(it, CardStatus.ACTIVE) }
            }
        }
    }

    /**
     * Returns true when ALL three aspects of [vocabId] have been mastered
     * ([GRADUATION_THRESHOLD] consecutive correct answers each).
     */
    fun shouldGraduate(vocabId: String): Boolean =
        ALL_ASPECTS.all { isAspectGraduated(vocabId, it) }

    /**
     * Graduates [vocabId] (ACTIVE → GRADUATED) and immediately promotes the
     * next NEW card from [allIds] so the active deck stays full.
     */
    fun graduateCard(vocabId: String, allIds: List<String>, deckSize: Int) {
        setCardStatus(vocabId, CardStatus.GRADUATED)
        val currentActiveCount = allIds.count { getCardStatus(it) == CardStatus.ACTIVE }
        if (currentActiveCount < deckSize) {
            allIds.firstOrNull { getCardStatus(it) == CardStatus.NEW }
                ?.let { setCardStatus(it, CardStatus.ACTIVE) }
        }
    }

    // ── Aspect-specific storage keys ──────────────────────────────────────────

    private fun repsKey(vocabId: String, aspect: AspectType) = "${vocabId}_${aspect.key}_reps"
    private fun intervalKey(vocabId: String, aspect: AspectType) = "${vocabId}_${aspect.key}_interval"
    private fun nextReviewKey(vocabId: String, aspect: AspectType) = "${vocabId}_${aspect.key}_next_review"
    private fun easeKey(vocabId: String, aspect: AspectType) = "${vocabId}_${aspect.key}_ease"

    // ── Aspect-specific queries ───────────────────────────────────────────────

    fun getAspectIntervalMs(vocabId: String, aspect: AspectType): Long =
        prefs.getLong(intervalKey(vocabId, aspect), 0L)

    fun getAspectNextReviewMs(vocabId: String, aspect: AspectType): Long =
        prefs.getLong(nextReviewKey(vocabId, aspect), 0L)

    /** True when this aspect has never been answered or its due timestamp has passed. */
    fun isAspectDue(vocabId: String, aspect: AspectType): Boolean =
        getAspectNextReviewMs(vocabId, aspect) <= System.currentTimeMillis()

    /** True when this aspect has reached [GRADUATION_THRESHOLD] consecutive correct answers. */
    fun isAspectGraduated(vocabId: String, aspect: AspectType): Boolean =
        prefs.getInt(repsKey(vocabId, aspect), 0) >= GRADUATION_THRESHOLD

    /**
     * True when the card has at least one aspect that is currently due.
     * Used to filter the active deck down to cards that need reviewing today.
     */
    fun isDue(vocabId: String): Boolean =
        ALL_ASPECTS.any { isAspectDue(vocabId, it) }

    /**
     * Returns the earliest future due-timestamp across all [vocabIds] and all
     * aspects, or null if every (vocab, aspect) pair is already due.
     */
    fun nextDueAfterNow(vocabIds: List<String>): Long? {
        val now = System.currentTimeMillis()
        return vocabIds
            .flatMap { id -> ALL_ASPECTS.map { getAspectNextReviewMs(id, it) } }
            .filter { it > now }
            .minOrNull()
    }

    // ── Answer recording ──────────────────────────────────────────────────────

    fun recordAnswer(vocabId: String, aspect: AspectType, correct: Boolean) {
        val now = System.currentTimeMillis()
        val intervalMs = getAspectIntervalMs(vocabId, aspect)
        val reps = prefs.getInt(repsKey(vocabId, aspect), 0)
        val ease = prefs.getFloat(easeKey(vocabId, aspect), DEFAULT_EASE)

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
            .putLong(intervalKey(vocabId, aspect), newIntervalMs)
            .putLong(nextReviewKey(vocabId, aspect), now + newIntervalMs)
            .putInt(repsKey(vocabId, aspect), newReps)
            .putFloat(easeKey(vocabId, aspect), newEase)
            .apply()
    }

    // ── Formatting helpers ────────────────────────────────────────────────────

    /** Human-readable interval for a specific aspect (e.g. "New", "5m", "2h 10m"). */
    fun formatAspectInterval(vocabId: String, aspect: AspectType): String {
        val ms = getAspectIntervalMs(vocabId, aspect)
        return if (ms == 0L) "New" else formatMs(ms)
    }

    fun formatMs(ms: Long): String {
        val minutes = ms / 60_000
        val hours = minutes / 60
        val days = hours / 24
        return when {
            days > 0 && hours % 24 > 0 -> "${days}d ${hours % 24}h"
            days > 0 -> "${days}d"
            hours > 0 && minutes % 60 > 0 -> "${hours}h ${minutes % 60}m"
            hours > 0 -> "${hours}h"
            minutes > 0 -> "${minutes}m"
            else -> "<1m"
        }
    }
}
