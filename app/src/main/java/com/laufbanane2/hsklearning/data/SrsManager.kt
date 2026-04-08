package com.laufbanane2.hsklearning.data

import android.content.Context

/**
 * Spaced-repetition scheduler using fixed levels (1–6).
 *
 * Each vocabulary card has three independently-scheduled aspects:
 *  - READING        – recognise the Chinese word (no audio)
 *  - LISTENING      – translate the spoken sentence (audio only)
 *  - READING_SENTENCE – translate the written Chinese sentence (no pinyin)
 *
 * Each aspect progresses through 6 levels independently:
 *  Level 0 (new): not yet studied; always due.
 *  Level 1:  1 day
 *  Level 2:  2 days
 *  Level 3:  4 days
 *  Level 4:  8 days
 *  Level 5: 16 days
 *  Level 6: mature (32 days); no longer shown for review.
 *
 * Correct answer → aspect level +1.
 * Wrong answer   → aspect level resets to 1.
 *
 * A card becomes MATURE (IN_PROGRESS → MATURE) once ALL three aspects reach level 6.
 *
 * Active/in-progress deck:
 *  Only IN_PROGRESS cards are shown during normal study. A card is promoted from
 *  NEW to IN_PROGRESS when an empty slot in the active deck is available.
 *  The deck stays full by immediately promoting the next NEW card after a card matures.
 *  If the deck size is lowered, the least-progressed IN_PROGRESS cards are demoted to NEW.
 */
class SrsManager(context: Context) {

    private val prefs = context.getSharedPreferences("srs_data", Context.MODE_PRIVATE)

    enum class CardStatus { NEW, IN_PROGRESS, MATURE }

    /** The three independently-tracked study aspects for every vocabulary card. */
    enum class AspectType(val key: String) {
        READING("reading"),
        LISTENING("listening"),
        READING_SENTENCE("reading_sentence")
    }

    companion object {
        /**
         * Review intervals in milliseconds indexed by level.
         * Level 0 is the "new" state (never studied); its interval is unused since level-0
         * aspects are always considered due.
         */
        val LEVEL_INTERVALS_MS = longArrayOf(
            0L,             // Level 0: new (always due)
            86_400_000L,    // Level 1:  1 day
            172_800_000L,   // Level 2:  2 days
            345_600_000L,   // Level 3:  4 days
            691_200_000L,   // Level 4:  8 days
            1_382_400_000L, // Level 5: 16 days
            2_764_800_000L  // Level 6: mature (32 days, not reviewed)
        )
        const val MATURE_LEVEL = 6
        val ALL_ASPECTS: List<AspectType> = AspectType.values().toList()
    }

    // ── Card status ───────────────────────────────────────────────────────────

    fun getCardStatus(vocabId: String): CardStatus =
        when (prefs.getString("${vocabId}_status", "new")) {
            "in_progress", "active" -> CardStatus.IN_PROGRESS
            "mature", "graduated"   -> CardStatus.MATURE
            else                    -> CardStatus.NEW
        }

    private fun setCardStatus(vocabId: String, status: CardStatus) {
        val str = when (status) {
            CardStatus.NEW         -> "new"
            CardStatus.IN_PROGRESS -> "in_progress"
            CardStatus.MATURE      -> "mature"
        }
        prefs.edit().putString("${vocabId}_status", str).apply()
    }

    /** Returns all IDs from [allIds] whose status is [CardStatus.IN_PROGRESS]. */
    fun getActiveIds(allIds: List<String>): List<String> =
        allIds.filter { getCardStatus(it) == CardStatus.IN_PROGRESS }

    /**
     * Ensures the active deck has exactly [deckSize] cards.
     * - If there are fewer IN_PROGRESS cards than [deckSize], promotes NEW cards to fill slots.
     * - If there are more IN_PROGRESS cards than [deckSize] (e.g. the user lowered the setting),
     *   demotes the excess back to NEW, preferring cards with the least total level progress.
     * MATURE cards are never touched.
     */
    fun initializeActiveDeck(allIds: List<String>, deckSize: Int) {
        val activeIds = allIds.filter { getCardStatus(it) == CardStatus.IN_PROGRESS }
        val currentActiveCount = activeIds.size

        if (currentActiveCount > deckSize) {
            // Demote excess cards; prefer those with the least total level progress.
            val excess = currentActiveCount - deckSize
            activeIds
                .sortedBy { id -> ALL_ASPECTS.sumOf { aspect -> getAspectLevel(id, aspect) } }
                .take(excess)
                .forEach { setCardStatus(it, CardStatus.NEW) }
        } else {
            val slotsToFill = deckSize - currentActiveCount
            if (slotsToFill > 0) {
                allIds
                    .filter { getCardStatus(it) == CardStatus.NEW }
                    .take(slotsToFill)
                    .forEach { setCardStatus(it, CardStatus.IN_PROGRESS) }
            }
        }
    }

    /**
     * Returns true when ALL three aspects of [vocabId] have reached [MATURE_LEVEL].
     */
    fun shouldMature(vocabId: String): Boolean =
        ALL_ASPECTS.all { isAspectMature(vocabId, it) }

    /**
     * Matures [vocabId] (IN_PROGRESS → MATURE) and immediately promotes the
     * next NEW card from [allIds] so the active deck stays full.
     */
    fun matureCard(vocabId: String, allIds: List<String>, deckSize: Int) {
        setCardStatus(vocabId, CardStatus.MATURE)
        val currentActiveCount = allIds.count { getCardStatus(it) == CardStatus.IN_PROGRESS }
        if (currentActiveCount < deckSize) {
            allIds.firstOrNull { getCardStatus(it) == CardStatus.NEW }
                ?.let { setCardStatus(it, CardStatus.IN_PROGRESS) }
        }
    }

    // ── Aspect-specific storage keys ──────────────────────────────────────────

    private fun levelKey(vocabId: String, aspect: AspectType) = "${vocabId}_${aspect.key}_level"
    private fun nextReviewKey(vocabId: String, aspect: AspectType) = "${vocabId}_${aspect.key}_next_review"

    // ── Aspect-specific queries ───────────────────────────────────────────────

    /** Returns the current SRS level (0–6) for the given aspect. */
    fun getAspectLevel(vocabId: String, aspect: AspectType): Int =
        prefs.getInt(levelKey(vocabId, aspect), 0)

    fun getAspectNextReviewMs(vocabId: String, aspect: AspectType): Long =
        prefs.getLong(nextReviewKey(vocabId, aspect), 0L)

    /** True when this aspect has reached [MATURE_LEVEL] and should no longer be reviewed. */
    fun isAspectMature(vocabId: String, aspect: AspectType): Boolean =
        getAspectLevel(vocabId, aspect) >= MATURE_LEVEL

    /**
     * True when this aspect is due for review.
     * Level-0 aspects are always due; mature aspects are never due;
     * all others are due when their next-review timestamp has passed.
     */
    fun isAspectDue(vocabId: String, aspect: AspectType): Boolean {
        val level = getAspectLevel(vocabId, aspect)
        if (level >= MATURE_LEVEL) return false
        if (level == 0) return true
        return getAspectNextReviewMs(vocabId, aspect) <= System.currentTimeMillis()
    }

    /**
     * True when the card has at least one aspect that is currently due.
     * Used to filter the active deck down to cards that need reviewing today.
     */
    fun isDue(vocabId: String): Boolean =
        ALL_ASPECTS.any { isAspectDue(vocabId, it) }

    /**
     * Returns the earliest future due-timestamp across all [vocabIds] and all
     * non-mature aspects, or null if every due aspect is already past due.
     */
    fun nextDueAfterNow(vocabIds: List<String>): Long? {
        val now = System.currentTimeMillis()
        return vocabIds
            .flatMap { id ->
                ALL_ASPECTS
                    .filter { aspect -> !isAspectMature(id, aspect) }
                    .map { aspect -> getAspectNextReviewMs(id, aspect) }
            }
            .filter { it > now }
            .minOrNull()
    }

    // ── Answer recording ──────────────────────────────────────────────────────

    fun recordAnswer(vocabId: String, aspect: AspectType, correct: Boolean) {
        val now = System.currentTimeMillis()
        val level = getAspectLevel(vocabId, aspect)

        val newLevel = if (correct) (level + 1).coerceAtMost(MATURE_LEVEL) else 0
        val newNextReview = if (newLevel == 0) 0L else now + LEVEL_INTERVALS_MS[newLevel]

        prefs.edit()
            .putInt(levelKey(vocabId, aspect), newLevel)
            .putLong(nextReviewKey(vocabId, aspect), newNextReview)
            .apply()
    }

    // ── Formatting helpers ────────────────────────────────────────────────────

    /** Human-readable level label for a specific aspect (e.g. "New", "Level 3", "Mature"). */
    fun formatAspectLevel(vocabId: String, aspect: AspectType): String {
        val level = getAspectLevel(vocabId, aspect)
        return when {
            level == 0            -> "New"
            level >= MATURE_LEVEL -> "Mature"
            else                  -> "Level $level"
        }
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
