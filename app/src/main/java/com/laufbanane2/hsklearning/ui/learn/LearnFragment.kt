package com.laufbanane2.hsklearning.ui.learn

import android.content.Context
import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
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

    private var vocabList: List<VocabItem> = emptyList()
    private var currentIndex = 0
    private var currentItem: VocabItem? = null

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

    override fun onResume() {
        super.onResume()
        loadVocab()
    }

    private fun initTts() {
        tts = TextToSpeech(requireContext()) { status ->
            if (status == TextToSpeech.SUCCESS) {
                val result = tts?.setLanguage(Locale.SIMPLIFIED_CHINESE)
                ttsReady = result != TextToSpeech.LANG_MISSING_DATA &&
                        result != TextToSpeech.LANG_NOT_SUPPORTED
                tts?.setSpeechRate(0.85f)
                tts?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                    override fun onStart(utteranceId: String?) {}
                    override fun onDone(utteranceId: String?) {}
                    @Deprecated("Deprecated in Java")
                    override fun onError(utteranceId: String?) {}
                })
                currentItem?.let { speakSentence(it.sentence) }
            }
        }
    }

    private fun speakSentence(sentence: String) {
        if (ttsReady) {
            tts?.speak(sentence, TextToSpeech.QUEUE_FLUSH, null, "sentence_${System.currentTimeMillis()}")
        }
    }

    private fun loadVocab() {
        val prefs = requireContext().getSharedPreferences("settings", Context.MODE_PRIVATE)
        val hsk1 = prefs.getBoolean("hsk1_enabled", true)
        val hsk2 = prefs.getBoolean("hsk2_enabled", false)
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
        binding.textChinese.isClickable = true
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
        tts?.stop()
        tts?.shutdown()
        tts = null
        _binding = null
    }
}
