package com.laufbanane2.hsklearning.ui.learn

import android.content.Context
import android.media.MediaPlayer
import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import com.laufbanane2.hsklearning.data.ElevenLabsClient
import com.laufbanane2.hsklearning.data.StatsManager
import com.laufbanane2.hsklearning.data.VocabData
import com.laufbanane2.hsklearning.data.VocabItem
import com.laufbanane2.hsklearning.databinding.FragmentLearnBinding
import java.io.File
import java.util.Locale

class LearnFragment : Fragment() {

    private var _binding: FragmentLearnBinding? = null
    private val binding get() = _binding!!

    private lateinit var statsManager: StatsManager
    private var tts: TextToSpeech? = null
    private var ttsReady = false
    private var mediaPlayer: MediaPlayer? = null
    private var elevenLabsClient: ElevenLabsClient? = null
    private var cachedApiKey: String = ""

    // Monotonically increasing ID for the "current" audio request.
    // Any callback that arrives with a stale ID is discarded, preventing
    // ElevenLabs and the TTS fallback from playing simultaneously.
    private var currentUtteranceId = 0

    private var vocabList: List<VocabItem> = emptyList()
    private var currentIndex = 0
    private var currentItem: VocabItem? = null

    // Settings that were in effect the last time loadVocab() ran.
    // Used to avoid reshuffling the deck when the user simply switches away
    // to another app and comes back (Problem 1).
    private var loadedHsk1 = false
    private var loadedHsk2 = false
    private var vocabLoaded = false

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
    // to another app and returns (Problem 1).
    override fun onResume() {
        super.onResume()
        val prefs = requireContext().getSharedPreferences("settings", Context.MODE_PRIVATE)
        val hsk1 = prefs.getBoolean("hsk1_enabled", true)
        val hsk2 = prefs.getBoolean("hsk2_enabled", false)
        if (!vocabLoaded || hsk1 != loadedHsk1 || hsk2 != loadedHsk2) {
            loadVocab()
        }
    }

    private fun initTts() {
        tts = TextToSpeech(requireContext()) { status ->
            if (status == TextToSpeech.SUCCESS) {
                val result = tts?.setLanguage(Locale.SIMPLIFIED_CHINESE)
                ttsReady = result != TextToSpeech.LANG_MISSING_DATA &&
                        result != TextToSpeech.LANG_NOT_SUPPORTED
                tts?.setSpeechRate(0.85f)
                // Do NOT call speakSentence here – showCurrentWord() already
                // triggered it, and calling it again would cause a double-play
                // (Problem 3).
            }
        }
    }

    // Stop whatever audio is currently active (ElevenLabs MediaPlayer or TTS).
    private fun stopCurrentAudio() {
        tts?.stop()
        mediaPlayer?.apply {
            if (isPlaying) stop()
            release()
        }
        mediaPlayer = null
    }

    // Entry point for all audio playback.
    // Increments the utterance ID so that any in-flight callbacks for the
    // previous word are silently discarded when they arrive (Problem 3).
    private fun speakSentence(sentence: String) {
        val utteranceId = ++currentUtteranceId
        stopCurrentAudio()

        val apiKey = requireContext()
            .getSharedPreferences("settings", Context.MODE_PRIVATE)
            .getString("elevenlabs_api_key", "") ?: ""

        if (apiKey.isNotBlank()) {
            if (elevenLabsClient == null || apiKey != cachedApiKey) {
                elevenLabsClient = ElevenLabsClient(apiKey)
                cachedApiKey = apiKey
            }
            elevenLabsClient!!.generateSpeech(
                text = sentence,
                onAudioBytes = { bytes ->
                    // Discard if the user has already moved to the next word.
                    if (utteranceId == currentUtteranceId) {
                        playAudioBytes(bytes)
                    }
                },
                onError = {
                    // ElevenLabs failed – fall back to device TTS.
                    if (utteranceId == currentUtteranceId) {
                        speakWithTts(sentence)
                    }
                }
            )
        } else {
            speakWithTts(sentence)
        }
    }

    private fun speakWithTts(sentence: String) {
        if (ttsReady) {
            tts?.speak(sentence, TextToSpeech.QUEUE_FLUSH, null, "sentence_${System.currentTimeMillis()}")
        }
    }

    private fun playAudioBytes(bytes: ByteArray) {
        // Use a unique filename per request to prevent overwriting a file that is
        // still being played back by a concurrent (now-stale) MediaPlayer.
        val tempFile = File(requireContext().cacheDir, "elevenlabs_${System.currentTimeMillis()}.mp3")
        tempFile.writeBytes(bytes)
        activity?.runOnUiThread {
            stopCurrentAudio()
            try {
                mediaPlayer = MediaPlayer().apply {
                    setDataSource(tempFile.absolutePath)
                    setOnCompletionListener {
                        it.release()
                        tempFile.delete()
                        if (mediaPlayer == it) mediaPlayer = null
                    }
                    prepare()
                    start()
                }
            } catch (e: Exception) {
                tempFile.delete()
                // If playback fails, fall back to TTS for the current item.
                currentItem?.let { speakWithTts(it.sentence) }
            }
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

