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
import com.laufbanane2.hsklearning.R
import com.laufbanane2.hsklearning.data.ChineseFont
import com.laufbanane2.hsklearning.data.ChineseFonts
import com.laufbanane2.hsklearning.data.VocabData
import com.laufbanane2.hsklearning.databinding.FragmentSettingsBinding

class SettingsFragment : Fragment() {

    private var _binding: FragmentSettingsBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentSettingsBinding.inflate(inflater, container, false)
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

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}

