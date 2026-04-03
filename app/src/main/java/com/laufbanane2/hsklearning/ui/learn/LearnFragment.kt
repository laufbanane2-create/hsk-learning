package com.laufbanane2.hsklearning.ui.learn

import android.content.Context
import android.graphics.Typeface
import android.media.MediaPlayer
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.speech.tts.TextToSpeech
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.provider.FontRequest
import androidx.core.provider.FontsContractCompat
import androidx.fragment.app.Fragment
import com.laufbanane2.hsklearning.R
import com.laufbanane2.hsklearning.data.ChineseFonts
import com.laufbanane2.hsklearning.data.StatsManager
import com.laufbanane2.hsklearning.data.VocabData
import com.laufbanane2.hsklearning.data.VocabItem
import com.laufbanane2.hsklearning.databinding.FragmentLearnBinding
import java.util.Locale

class LearnFragment : Fragment() {

    private var _binding: FragmentLearnBinding? = null
    private val binding get() = _binding!!

    private lateinit var statsManager: StatsManager
    private var tts: TextToSpeech? = null
    private var ttsReady = false
    private var mediaPlayer: MediaPlayer? = null

    private var vocabList: List<VocabItem> = emptyList()
    private var currentIndex = 0
    private var currentItem: VocabItem? = null

    // Settings that were in effect the last time loadVocab() ran.
    // Used to avoid reshuffling the deck when the user simply switches away
    // to another app and comes back.
    private var loadedHsk1 = false
    private var loadedHsk2 = false
    private var vocabLoaded = false

    // Loaded Chinese typefaces; populated asynchronously at startup.
    // All mutations happen on the main-thread Handler passed to FontsContractCompat,
    // and all reads happen in showCurrentWord() on the main thread, so no
    // synchronisation is needed.
    private val chineseTypefaces = mutableListOf<Typeface>()

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

        initTts()
        loadChineseFonts()
        setupMuteButton()

        binding.buttonShow.setOnClickListener { revealAnswer() }
        binding.textChinese.setOnClickListener { currentItem?.let { speakSentence(it.sentence) } }
        binding.buttonRight.setOnClickListener { handleAnswer(correct = true) }
        binding.buttonWrong.setOnClickListener { handleAnswer(correct = false) }
        binding.buttonRestart.setOnClickListener { loadVocab() }
    }

    // Only reload vocab when either:
    //  • it hasn't been loaded yet (fresh fragment after a tab switch), or
    //  • the user changed the HSK-level settings while away.
    // This prevents a new word from appearing whenever the user multi-tasks
    // to another app and returns.
    override fun onResume() {
        super.onResume()
        val prefs = requireContext().getSharedPreferences("settings", Context.MODE_PRIVATE)
        val hsk1 = prefs.getBoolean("hsk1_enabled", true)
        val hsk2 = prefs.getBoolean("hsk2_enabled", false)
        if (!vocabLoaded || hsk1 != loadedHsk1 || hsk2 != loadedHsk2) {
            loadVocab()
        }
        // Always reload fonts on resume so changes made in Settings are picked up.
        loadChineseFonts()
    }

    private fun isMuted(): Boolean {
        val prefs = requireContext().getSharedPreferences("settings", Context.MODE_PRIVATE)
        return prefs.getBoolean("muted", false)
    }

    private fun setupMuteButton() {
        // updateMuteIcon() runs here, before the first frame, so the icon
        // always reflects the persisted state even if the user previously muted.
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

    // Request the Chinese fonts from the Google Fonts provider asynchronously.
    // Only fonts enabled in settings are requested.
    // Each font that loads successfully is added to chineseTypefaces and will
    // be picked up the next time a new word is shown.
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
                        override fun onTypefaceRequestFailed(reason: Int) {
                            // Font unavailable (no network / no Play Services) — skip it.
                        }
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

    // Stop whatever audio is currently active.
    private fun stopCurrentAudio() {
        tts?.stop()
        mediaPlayer?.apply {
            if (isPlaying) stop()
            release()
        }
        mediaPlayer = null
    }

    // Entry point for all audio playback.
    //
    // Priority:
    //  1. Bundled raw resource MP3 (pre-generated at build time via
    //     `./gradlew generateAudio`) — zero network, zero API key required.
    //  2. Android device TextToSpeech fallback.
    private fun speakSentence(sentence: String) {
        if (isMuted()) return
        stopCurrentAudio()

        // 1. Try the bundled pre-generated MP3 for this vocabulary item.
        val vocabId = currentItem?.id
        if (vocabId != null) {
            val resId = resources.getIdentifier(vocabId, "raw", requireContext().packageName)
            if (resId != 0) {
                playRawResource(resId)
                return
            }
        }

        // 2. Device TTS as fallback.
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
                // Bundled file unplayable — log and fall back to TTS.
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

    private fun loadVocab() {
        val prefs = requireContext().getSharedPreferences("settings", Context.MODE_PRIVATE)
        val hsk1 = prefs.getBoolean("hsk1_enabled", true)
        val hsk2 = prefs.getBoolean("hsk2_enabled", false)
        loadedHsk1 = hsk1
        loadedHsk2 = hsk2
        vocabLoaded = true
        vocabList = VocabData.getVocab(hsk1, hsk2).shuffled()
        currentIndex = 0

        if (vocabList.isEmpty()) {
            showEmptyState()
        } else {
            showCurrentWord()
        }
    }

    private fun showEmptyState() {
        binding.groupCard.visibility = View.GONE
        binding.groupEmpty.visibility = View.VISIBLE
    }

    private fun showCurrentWord() {
        if (currentIndex >= vocabList.size) {
            showFinished()
            return
        }
        currentItem = vocabList[currentIndex]
        val item = currentItem ?: return

        binding.groupCard.visibility = View.VISIBLE
        binding.groupEmpty.visibility = View.GONE
        binding.groupFinished.visibility = View.GONE

        binding.textProgress.text = "${currentIndex + 1} / ${vocabList.size}"
        binding.textLevelBadge.text = "HSK ${item.level}"
        binding.textChinese.text = item.chinese
        if (chineseTypefaces.isNotEmpty()) {
            binding.textChinese.typeface = chineseTypefaces.random()
        }
        binding.buttonShow.visibility = View.VISIBLE
        binding.buttonShow.isEnabled = true

        binding.groupAnswer.visibility = View.GONE
        binding.groupActions.visibility = View.GONE

        val correct = statsManager.getCorrect(item.id)
        val wrong = statsManager.getWrong(item.id)
        binding.textStats.text = "✓ $correct   ✗ $wrong"

        speakSentence(item.sentence)
    }

    private fun revealAnswer() {
        val item = currentItem ?: return
        binding.buttonShow.visibility = View.GONE

        binding.textEnglish.text = item.english
        binding.textSentenceChinese.text = item.sentence
        binding.textSentencePinyin.text = item.sentencePinyin
        binding.textSentenceEnglish.text = item.sentenceEnglish
        binding.textPinyin.text = item.pinyin

        binding.groupAnswer.visibility = View.VISIBLE
        binding.groupActions.visibility = View.VISIBLE
    }

    private fun handleAnswer(correct: Boolean) {
        val item = currentItem ?: return
        if (correct) {
            statsManager.incrementCorrect(item.id)
        } else {
            statsManager.incrementWrong(item.id)
        }
        val c = statsManager.getCorrect(item.id)
        val w = statsManager.getWrong(item.id)
        binding.textStats.text = "✓ $c   ✗ $w"

        currentIndex++
        showCurrentWord()
    }

    private fun showFinished() {
        binding.groupCard.visibility = View.GONE
        binding.groupEmpty.visibility = View.GONE
        binding.groupFinished.visibility = View.VISIBLE
    }

    override fun onDestroyView() {
        super.onDestroyView()
        stopCurrentAudio()
        tts?.shutdown()
        tts = null
        _binding = null
    }
}
