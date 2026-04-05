package com.laufbanane2.hsklearning.ui.learn

import android.content.Context
import android.graphics.Typeface
import android.media.MediaPlayer
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.speech.tts.TextToSpeech
import android.util.TypedValue
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.provider.FontRequest
import androidx.core.provider.FontsContractCompat
import androidx.fragment.app.Fragment
import com.google.android.material.snackbar.Snackbar
import com.laufbanane2.hsklearning.R
import com.laufbanane2.hsklearning.data.ChineseFonts
import com.laufbanane2.hsklearning.data.SrsManager
import com.laufbanane2.hsklearning.data.StatsManager
import com.laufbanane2.hsklearning.data.VocabData
import com.laufbanane2.hsklearning.data.VocabItem
import com.laufbanane2.hsklearning.databinding.FragmentLearnBinding
import java.util.Locale

class LearnFragment : Fragment() {

    private var _binding: FragmentLearnBinding? = null
    private val binding get() = _binding!!

    private lateinit var statsManager: StatsManager
    private lateinit var srsManager: SrsManager
    private var tts: TextToSpeech? = null
    private var ttsReady = false
    private var mediaPlayer: MediaPlayer? = null

    /** A vocabulary item paired with the aspect being tested in this session slot. */
    private data class AspectCard(val item: VocabItem, val aspect: SrsManager.AspectType)

    private var vocabList: List<AspectCard> = emptyList()
    private var allVocab: List<VocabItem> = emptyList()
    private var currentIndex = 0
    private var currentAspectCard: AspectCard? = null
    // Convenience accessor used by speakSentence() to look up the raw audio resource.
    private val currentItem: VocabItem? get() = currentAspectCard?.item
    // Cached count of active cards; updated in loadVocab and after each graduation.
    private var activeDeckCount = 0

    // Settings that were in effect the last time loadVocab() ran.
    private var loadedHsk1 = false
    private var loadedHsk2 = false
    private var loadedDeckSize = -1
    private var vocabLoaded = false

    // Loaded Chinese typefaces; populated asynchronously at startup.
    private val chineseTypefaces = mutableListOf<Typeface>()

    companion object {
        private const val DEFAULT_ACTIVE_DECK_SIZE = 10
        private const val TEXT_SIZE_WORD_SP = 96f
        private const val TEXT_SIZE_LISTEN_SP = 72f
        private const val TEXT_SIZE_SENTENCE_SP = 24f
    }

    // All vocab IDs for the currently loaded vocabulary set; kept in sync with allVocab.
    private var allVocabIds: List<String> = emptyList()

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentLearnBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        statsManager = StatsManager(requireContext())
        srsManager = SrsManager(requireContext())

        initTts()
        loadChineseFonts()
        setupMuteButton()

        binding.buttonShow.setOnClickListener { revealAnswer() }
        binding.textChinese.setOnClickListener { onChineseTextClicked() }
        binding.buttonRight.setOnClickListener { handleAnswer(correct = true) }
        binding.buttonWrong.setOnClickListener { handleAnswer(correct = false) }
        binding.buttonRestart.setOnClickListener { loadVocab() }
        binding.buttonStudyAll.setOnClickListener { loadVocab(reviewAll = true) }
    }

    override fun onResume() {
        super.onResume()
        val prefs = requireContext().getSharedPreferences("settings", Context.MODE_PRIVATE)
        val hsk1 = prefs.getBoolean("hsk1_enabled", true)
        val hsk2 = prefs.getBoolean("hsk2_enabled", false)
        val deckSize = prefs.getInt("active_deck_size", DEFAULT_ACTIVE_DECK_SIZE)
        if (!vocabLoaded || hsk1 != loadedHsk1 || hsk2 != loadedHsk2 || deckSize != loadedDeckSize) {
            loadVocab()
        }
        loadChineseFonts()
    }

    private fun isMuted(): Boolean {
        val prefs = requireContext().getSharedPreferences("settings", Context.MODE_PRIVATE)
        return prefs.getBoolean("muted", false)
    }

    private fun setupMuteButton() {
        updateMuteIcon()
        binding.buttonMute.setOnClickListener {
            val prefs = requireContext().getSharedPreferences("settings", Context.MODE_PRIVATE)
            val nowMuted = !prefs.getBoolean("muted", false)
            prefs.edit().putBoolean("muted", nowMuted).apply()
            updateMuteIcon()
            if (nowMuted) stopCurrentAudio()
        }
    }

    private fun updateMuteIcon() {
        val muted = isMuted()
        binding.buttonMute.setImageResource(
            if (muted) R.drawable.ic_volume_off else R.drawable.ic_volume_up
        )
        binding.buttonMute.contentDescription = getString(
            if (muted) R.string.cd_mute_off else R.string.cd_mute_on
        )
    }

    private fun loadChineseFonts() {
        chineseTypefaces.clear()
        val prefs = requireContext().getSharedPreferences("settings", Context.MODE_PRIVATE)
        val handler = Handler(Looper.getMainLooper())
        ChineseFonts.ALL
            .filter { ChineseFonts.isEnabled(prefs, it) }
            .forEach { font ->
                val request = FontRequest(
                    "com.google.android.gms.fonts",
                    "com.google.android.gms",
                    font.googleQuery,
                    R.array.com_google_android_gms_fonts_certs
                )
                FontsContractCompat.requestFont(
                    requireContext(),
                    request,
                    object : FontsContractCompat.FontRequestCallback() {
                        override fun onTypefaceRetrieved(typeface: Typeface) {
                            chineseTypefaces.add(typeface)
                        }
                        override fun onTypefaceRequestFailed(reason: Int) {}
                    },
                    handler
                )
            }
    }

    private fun initTts() {
        tts = TextToSpeech(requireContext()) { status ->
            if (status == TextToSpeech.SUCCESS) {
                val result = tts?.setLanguage(Locale.SIMPLIFIED_CHINESE)
                ttsReady = result != TextToSpeech.LANG_MISSING_DATA &&
                        result != TextToSpeech.LANG_NOT_SUPPORTED
                tts?.setSpeechRate(0.85f)
            }
        }
    }

    private fun stopCurrentAudio() {
        tts?.stop()
        mediaPlayer?.apply {
            if (isPlaying) stop()
            release()
        }
        mediaPlayer = null
    }

    private fun speakSentence(sentence: String) {
        if (isMuted()) return
        stopCurrentAudio()

        val vocabId = currentItem?.id
        if (vocabId != null) {
            val resId = resources.getIdentifier(vocabId, "raw", requireContext().packageName)
            if (resId != 0) {
                playRawResource(resId)
                return
            }
        }

        speakWithTts(sentence)
    }

    private fun playRawResource(resId: Int) {
        activity?.runOnUiThread {
            stopCurrentAudio()
            try {
                mediaPlayer = MediaPlayer.create(requireContext(), resId)?.apply {
                    setOnCompletionListener {
                        it.release()
                        if (mediaPlayer == it) mediaPlayer = null
                    }
                    start()
                }
            } catch (e: Exception) {
                android.util.Log.e("LearnFragment", "Failed to play raw resource $resId", e)
                currentItem?.let { speakWithTts(it.sentence) }
            }
        }
    }

    private fun speakWithTts(sentence: String) {
        if (ttsReady) {
            tts?.speak(sentence, TextToSpeech.QUEUE_FLUSH, null, "sentence_${System.currentTimeMillis()}")
        }
    }

    /**
     * Called when the user taps the main Chinese text area.
     * Replays audio for LISTENING and READING_SENTENCE aspects; silent for READING.
     */
    private fun onChineseTextClicked() {
        val card = currentAspectCard ?: return
        if (card.aspect != SrsManager.AspectType.READING) {
            speakSentence(card.item.sentence)
        }
    }

    private fun loadVocab(reviewAll: Boolean = false) {
        val prefs = requireContext().getSharedPreferences("settings", Context.MODE_PRIVATE)
        val hsk1 = prefs.getBoolean("hsk1_enabled", true)
        val hsk2 = prefs.getBoolean("hsk2_enabled", false)
        val deckSize = prefs.getInt("active_deck_size", DEFAULT_ACTIVE_DECK_SIZE)
        loadedHsk1 = hsk1
        loadedHsk2 = hsk2
        loadedDeckSize = deckSize
        vocabLoaded = true

        allVocab = VocabData.getVocab(hsk1, hsk2)
        allVocabIds = allVocab.map { it.id }

        if (allVocab.isEmpty()) {
            vocabList = emptyList()
            showEmptyState()
            return
        }

        val allIds = allVocabIds

        srsManager.initializeActiveDeck(allIds, deckSize)
        activeDeckCount = srsManager.getActiveIds(allIds).size

        if (reviewAll) {
            // Review all (vocab, aspect) combinations in random order.
            vocabList = allVocab.flatMap { item ->
                SrsManager.ALL_ASPECTS.map { aspect -> AspectCard(item, aspect) }
            }.shuffled()
        } else {
            // Normal mode: for each ACTIVE card, add one AspectCard per due aspect.
            val activeIds = srsManager.getActiveIds(allIds).toSet()
            val aspectCards = mutableListOf<AspectCard>()
            for (item in allVocab) {
                if (item.id !in activeIds) continue
                for (aspect in SrsManager.ALL_ASPECTS) {
                    if (srsManager.isAspectDue(item.id, aspect)) {
                        aspectCards.add(AspectCard(item, aspect))
                    }
                }
            }
            vocabList = aspectCards.shuffled()
        }

        currentIndex = 0

        if (vocabList.isEmpty()) {
            showNoDueState(srsManager.getActiveIds(allIds))
        } else {
            showCurrentWord()
        }
    }

    private fun showEmptyState() {
        binding.groupCard.visibility = View.GONE
        binding.groupEmpty.visibility = View.VISIBLE
        binding.groupFinished.visibility = View.GONE
        binding.groupNoDue.visibility = View.GONE
    }

    private fun showNoDueState(allIds: List<String>) {
        binding.groupCard.visibility = View.GONE
        binding.groupEmpty.visibility = View.GONE
        binding.groupFinished.visibility = View.GONE
        binding.groupNoDue.visibility = View.VISIBLE

        val nextDue = srsManager.nextDueAfterNow(allIds)
        binding.textNoDueMessage.text = if (nextDue != null) {
            val diffMs = nextDue - System.currentTimeMillis()
            getString(R.string.no_due_message_future, srsManager.formatMs(diffMs))
        } else {
            getString(R.string.no_due_message_now)
        }
    }

    private fun showCurrentWord() {
        if (currentIndex >= vocabList.size) {
            showFinished()
            return
        }
        currentAspectCard = vocabList[currentIndex]
        val card = currentAspectCard ?: return
        val item = card.item

        binding.groupCard.visibility = View.VISIBLE
        binding.groupEmpty.visibility = View.GONE
        binding.groupFinished.visibility = View.GONE
        binding.groupNoDue.visibility = View.GONE

        binding.textProgress.text = getString(
            R.string.label_progress,
            currentIndex + 1,
            vocabList.size,
            activeDeckCount
        )

        // Show level + aspect type in the badge.
        val aspectLabel = getString(when (card.aspect) {
            SrsManager.AspectType.READING          -> R.string.aspect_reading
            SrsManager.AspectType.LISTENING        -> R.string.aspect_listening
            SrsManager.AspectType.READING_SENTENCE -> R.string.aspect_sentence
        })
        binding.textLevelBadge.text = "HSK ${item.level}  $aspectLabel"

        binding.buttonShow.visibility = View.VISIBLE
        binding.buttonShow.isEnabled = true
        binding.groupAnswer.visibility = View.GONE
        binding.groupActions.visibility = View.GONE

        val correct = statsManager.getCorrect(item.id)
        val wrong = statsManager.getWrong(item.id)
        binding.textStats.text = "✓ $correct   ✗ $wrong"
        binding.textNextReview.text = getString(
            R.string.label_interval,
            srsManager.formatAspectInterval(item.id, card.aspect)
        )

        when (card.aspect) {
            SrsManager.AspectType.READING -> {
                // Show the Chinese word only — no audio.
                binding.textChinese.text = item.chinese
                binding.textChinese.setTextSize(TypedValue.COMPLEX_UNIT_SP, TEXT_SIZE_WORD_SP)
                if (chineseTypefaces.isNotEmpty()) {
                    binding.textChinese.typeface = chineseTypefaces.random()
                }
            }
            SrsManager.AspectType.LISTENING -> {
                // Play the sentence audio; show a speaker icon as the prompt.
                binding.textChinese.text = "🔊"
                binding.textChinese.setTextSize(TypedValue.COMPLEX_UNIT_SP, TEXT_SIZE_LISTEN_SP)
                speakSentence(item.sentence)
            }
            SrsManager.AspectType.READING_SENTENCE -> {
                // Show the Chinese sentence without pinyin — no audio.
                binding.textChinese.text = item.sentence
                binding.textChinese.setTextSize(TypedValue.COMPLEX_UNIT_SP, TEXT_SIZE_SENTENCE_SP)
                if (chineseTypefaces.isNotEmpty()) {
                    binding.textChinese.typeface = chineseTypefaces.random()
                }
            }
        }
    }

    private fun revealAnswer() {
        val card = currentAspectCard ?: return
        val item = card.item
        binding.buttonShow.visibility = View.GONE

        binding.textEnglish.text = item.english
        binding.textSentenceChinese.text = item.sentence
        binding.textSentencePinyin.text = item.sentencePinyin
        binding.textSentenceEnglish.text = item.sentenceEnglish
        binding.textPinyin.text = item.pinyin

        binding.groupAnswer.visibility = View.VISIBLE
        binding.groupActions.visibility = View.VISIBLE

        // Play audio on reveal for READING_SENTENCE (as specified).
        // LISTENING already played audio at the start; READING is intentionally silent.
        if (card.aspect == SrsManager.AspectType.READING_SENTENCE) {
            speakSentence(item.sentence)
        }
    }

    private fun handleAnswer(correct: Boolean) {
        val card = currentAspectCard ?: return
        val item = card.item

        if (correct) {
            statsManager.incrementCorrect(item.id)
        } else {
            statsManager.incrementWrong(item.id)
        }
        srsManager.recordAnswer(item.id, card.aspect, correct)

        if (correct && srsManager.shouldGraduate(item.id)) {
            val prefs = requireContext().getSharedPreferences("settings", Context.MODE_PRIVATE)
            val deckSize = prefs.getInt("active_deck_size", DEFAULT_ACTIVE_DECK_SIZE)
            srsManager.graduateCard(item.id, allVocabIds, deckSize)
            activeDeckCount = srsManager.getActiveIds(allVocabIds).size
            Snackbar.make(binding.root, getString(R.string.word_graduated), Snackbar.LENGTH_SHORT).show()
        }

        val c = statsManager.getCorrect(item.id)
        val w = statsManager.getWrong(item.id)
        binding.textStats.text = "✓ $c   ✗ $w"
        binding.textNextReview.text = getString(
            R.string.label_interval,
            srsManager.formatAspectInterval(item.id, card.aspect)
        )

        currentIndex++
        showCurrentWord()
    }

    private fun showFinished() {
        binding.groupCard.visibility = View.GONE
        binding.groupEmpty.visibility = View.GONE
        binding.groupFinished.visibility = View.VISIBLE
        binding.groupNoDue.visibility = View.GONE
    }

    override fun onDestroyView() {
        super.onDestroyView()
        stopCurrentAudio()
        tts?.shutdown()
        tts = null
        _binding = null
    }
}
