package com.laufbanane2.hsklearning.ui.settings

import android.content.Context
import android.graphics.Typeface
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.CheckBox
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.core.provider.FontRequest
import androidx.core.provider.FontsContractCompat
import androidx.fragment.app.Fragment
import com.laufbanane2.hsklearning.BuildConfig
import com.laufbanane2.hsklearning.R
import com.laufbanane2.hsklearning.data.ChineseFont
import com.laufbanane2.hsklearning.data.ChineseFonts
import com.laufbanane2.hsklearning.data.SrsManager
import com.laufbanane2.hsklearning.data.VocabData
import com.laufbanane2.hsklearning.databinding.FragmentSettingsBinding

class SettingsFragment : Fragment() {

    private var _binding: FragmentSettingsBinding? = null
    private val binding get() = _binding!!
    private lateinit var srsManager: SrsManager

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentSettingsBinding.inflate(inflater, container, false)
        srsManager = SrsManager(requireContext())
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val prefs = requireContext().getSharedPreferences("settings", Context.MODE_PRIVATE)
        binding.checkboxHsk1.isChecked = prefs.getBoolean("hsk1_enabled", true)
        binding.checkboxHsk2.isChecked = prefs.getBoolean("hsk2_enabled", false)

        binding.checkboxHsk1.text = getString(R.string.hsk1_label, VocabData.hsk1.size)
        binding.checkboxHsk2.text = getString(R.string.hsk2_label, VocabData.hsk2.size)

        val saveListener = View.OnClickListener {
            val hsk1 = binding.checkboxHsk1.isChecked
            val hsk2 = binding.checkboxHsk2.isChecked
            if (!hsk1 && !hsk2) {
                Toast.makeText(requireContext(), "Please select at least one level.", Toast.LENGTH_SHORT).show()
                binding.checkboxHsk1.isChecked = true
                return@OnClickListener
            }
            prefs.edit()
                .putBoolean("hsk1_enabled", hsk1)
                .putBoolean("hsk2_enabled", hsk2)
                .apply()
            Toast.makeText(requireContext(), "Settings saved.", Toast.LENGTH_SHORT).show()
        }

        binding.checkboxHsk1.setOnClickListener(saveListener)
        binding.checkboxHsk2.setOnClickListener(saveListener)

        // Active deck size
        val deckSize = prefs.getInt("active_deck_size", 10)
        when (deckSize) {
            5    -> binding.radioDeck5.isChecked = true
            15   -> binding.radioDeck15.isChecked = true
            20   -> binding.radioDeck20.isChecked = true
            else -> binding.radioDeck10.isChecked = true
        }
        binding.radioGroupDeckSize.setOnCheckedChangeListener { _, checkedId ->
            val size = when (checkedId) {
                R.id.radioDeck5  -> 5
                R.id.radioDeck15 -> 15
                R.id.radioDeck20 -> 20
                else             -> 10
            }
            prefs.edit().putInt("active_deck_size", size).apply()
        }

        // Build font rows dynamically: [CheckBox] [tappable font-name label]
        val density = resources.displayMetrics.density
        val rowBottomMargin = (12 * density).toInt()

        ChineseFonts.ALL.forEach { font ->
            val row = LinearLayout(requireContext()).apply {
                orientation = LinearLayout.HORIZONTAL
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                ).also { it.bottomMargin = rowBottomMargin }
            }

            val checkbox = CheckBox(requireContext()).apply {
                tag = font.key
                isChecked = ChineseFonts.isEnabled(prefs, font)
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.WRAP_CONTENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                )
                setOnClickListener {
                    val enabledCount = ChineseFonts.ALL.count { f ->
                        binding.groupFontCheckboxes.findViewWithTag<CheckBox>(f.key)?.isChecked == true
                    }
                    if (enabledCount == 0) {
                        Toast.makeText(
                            requireContext(),
                            getString(R.string.toast_font_min_one),
                            Toast.LENGTH_SHORT
                        ).show()
                        isChecked = true
                        return@setOnClickListener
                    }
                    prefs.edit().putBoolean(font.key, isChecked).apply()
                }
            }

            val label = TextView(requireContext()).apply {
                text = font.displayName
                textSize = 18f
                layoutParams = LinearLayout.LayoutParams(
                    0,
                    LinearLayout.LayoutParams.WRAP_CONTENT,
                    1f
                ).also { it.marginStart = (8 * density).toInt() }
                // Tapping the label shows the font preview dialog.
                setOnClickListener {
                    showFontPreview(font)
                }
            }

            row.addView(checkbox)
            row.addView(label)
            binding.groupFontCheckboxes.addView(row)
        }

        binding.textBuildInfo.text =
            "v${BuildConfig.VERSION_NAME} · ${BuildConfig.GIT_BRANCH} · ${BuildConfig.GIT_COMMIT}"

        binding.buttonCheckUpdates.setOnClickListener {
            Toast.makeText(requireContext(), getString(R.string.update_checking), Toast.LENGTH_SHORT).show()
            (activity as? com.laufbanane2.hsklearning.MainActivity)?.checkForUpdateManually()
        }
    }

    private fun showFontPreview(font: ChineseFont) {
        val context = requireContext()
        val sampleText = getString(R.string.font_preview_sample)
        val dialogTitle = "${font.displayName} — ${getString(R.string.font_preview_title)}"

        // Build the preview TextView shown inside the dialog.
        val previewView = TextView(context).apply {
            val pad = (24 * resources.displayMetrics.density).toInt()
            setPadding(pad, pad, pad, pad)
            textSize = 32f
            text = getString(R.string.font_preview_loading)
        }

        val dialog = AlertDialog.Builder(context)
            .setTitle(dialogTitle)
            .setView(previewView)
            .setPositiveButton(android.R.string.ok, null)
            .show()

        // Load the font asynchronously; update the preview when ready.
        val request = FontRequest(
            "com.google.android.gms.fonts",
            "com.google.android.gms",
            font.googleQuery,
            R.array.com_google_android_gms_fonts_certs
        )
        val handler = Handler(Looper.getMainLooper())
        FontsContractCompat.requestFont(
            context,
            request,
            object : FontsContractCompat.FontRequestCallback() {
                override fun onTypefaceRetrieved(typeface: Typeface) {
                    if (dialog.isShowing) {
                        previewView.typeface = typeface
                        previewView.text = sampleText
                    }
                }
                override fun onTypefaceRequestFailed(reason: Int) {
                    if (dialog.isShowing) {
                        previewView.text = sampleText
                    }
                }
            },
            handler
        )
    }

    override fun onResume() {
        super.onResume()
        refreshStats()
    }

    private fun refreshStats() {
        val density = resources.displayMetrics.density
        val container = binding.groupStatsContainer
        container.removeAllViews()

        val categories = listOf(
            getString(R.string.hsk1_label, VocabData.hsk1.size) to VocabData.hsk1,
            getString(R.string.hsk2_label, VocabData.hsk2.size) to VocabData.hsk2
        )

        // Colours for the status chart
        val colorNew        = android.graphics.Color.parseColor("#9E9E9E")
        val colorInProgress = android.graphics.Color.parseColor("#FFA726")
        val colorMature     = android.graphics.Color.parseColor("#4CAF50")

        // Colours for the level distribution chart (L0 → L6)
        val levelColors = intArrayOf(
            android.graphics.Color.parseColor("#BDBDBD"), // L0 grey
            android.graphics.Color.parseColor("#EF9A9A"), // L1 light red
            android.graphics.Color.parseColor("#FFCC80"), // L2 light orange
            android.graphics.Color.parseColor("#FFF59D"), // L3 light yellow
            android.graphics.Color.parseColor("#C5E1A5"), // L4 light green
            android.graphics.Color.parseColor("#80DEEA"), // L5 light teal
            android.graphics.Color.parseColor("#4CAF50")  // L6 mature green
        )
        val levelLabels = listOf(
            getString(R.string.stats_level_new),
            getString(R.string.stats_level_1),
            getString(R.string.stats_level_2),
            getString(R.string.stats_level_3),
            getString(R.string.stats_level_4),
            getString(R.string.stats_level_5),
            getString(R.string.stats_level_mature)
        )

        categories.forEach { (label, vocab) ->
            // ── Count status ────────────────────────────────────────────────
            var newCount = 0; var activeCount = 0; var matureCount = 0
            vocab.forEach { item ->
                when (srsManager.getCardStatus(item.id)) {
                    SrsManager.CardStatus.NEW         -> newCount++
                    SrsManager.CardStatus.IN_PROGRESS -> activeCount++
                    SrsManager.CardStatus.MATURE      -> matureCount++
                }
            }

            // ── Count aspect levels (0–6) across all aspects of all cards ──
            val levelCounts = IntArray(7)
            vocab.forEach { item ->
                SrsManager.ALL_ASPECTS.forEach { aspect ->
                    levelCounts[srsManager.getAspectLevel(item.id, aspect)]++
                }
            }

            // ── Build expandable section ────────────────────────────────────
            val section = LinearLayout(requireContext()).apply {
                orientation = LinearLayout.VERTICAL
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                ).also { it.bottomMargin = (8 * density).toInt() }
            }

            // Content panel (hidden by default)
            val content = LinearLayout(requireContext()).apply {
                orientation = LinearLayout.VERTICAL
                visibility = android.view.View.GONE
            }

            // Header row: label + toggle arrow
            val header = LinearLayout(requireContext()).apply {
                orientation = LinearLayout.HORIZONTAL
                val pad = (8 * density).toInt()
                setPadding(0, pad, 0, pad)
                isClickable = true
                isFocusable = true
                val rippleAttr = android.util.TypedValue()
                requireContext().theme.resolveAttribute(
                    android.R.attr.selectableItemBackground, rippleAttr, true
                )
                setBackgroundResource(rippleAttr.resourceId)
            }
            val headerLabel = TextView(requireContext()).apply {
                text = label
                textSize = 15f
                setTypeface(typeface, android.graphics.Typeface.BOLD)
                layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
            }
            val arrow = TextView(requireContext()).apply {
                text = "▶"
                textSize = 14f
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.WRAP_CONTENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                )
            }
            header.addView(headerLabel)
            header.addView(arrow)
            header.setOnClickListener {
                val expanding = content.visibility == android.view.View.GONE
                content.visibility = if (expanding) android.view.View.VISIBLE else android.view.View.GONE
                arrow.text = if (expanding) "▼" else "▶"
            }

            // Two pie charts side by side inside the content panel
            val chartsRow = LinearLayout(requireContext()).apply {
                orientation = LinearLayout.HORIZONTAL
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                ).also { it.bottomMargin = (8 * density).toInt() }
            }

            val statusChart = PieChartView(requireContext()).apply {
                layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
                    .also { it.marginEnd = (8 * density).toInt() }
                setData(
                    getString(R.string.stats_chart_status),
                    listOf(
                        PieChartView.Entry("New", colorNew, newCount),
                        PieChartView.Entry("In progress", colorInProgress, activeCount),
                        PieChartView.Entry("Mature", colorMature, matureCount)
                    )
                )
            }

            val levelEntries = (0..6).map { lvl ->
                PieChartView.Entry(levelLabels[lvl], levelColors[lvl], levelCounts[lvl])
            }
            val levelChart = PieChartView(requireContext()).apply {
                layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
                    .also { it.marginStart = (8 * density).toInt() }
                setData(getString(R.string.stats_chart_levels), levelEntries)
            }

            chartsRow.addView(statusChart)
            chartsRow.addView(levelChart)

            // Summary text line
            val summaryLine = getString(
                R.string.stats_category_line,
                label, newCount, activeCount, matureCount, vocab.size
            )
            val summaryView = TextView(requireContext()).apply {
                text = summaryLine
                textSize = 13f
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                ).also { it.bottomMargin = (8 * density).toInt() }
            }

            content.addView(chartsRow)
            content.addView(summaryView)

            section.addView(header)
            section.addView(content)
            container.addView(section)
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}

