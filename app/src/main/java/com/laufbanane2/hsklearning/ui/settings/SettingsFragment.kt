package com.laufbanane2.hsklearning.ui.settings

import android.content.Context
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import com.laufbanane2.hsklearning.data.ElevenLabsClient
import com.laufbanane2.hsklearning.databinding.FragmentSettingsBinding

class SettingsFragment : Fragment() {

    private var _binding: FragmentSettingsBinding? = null
    private val binding get() = _binding!!

    private var elevenLabsClient: ElevenLabsClient? = null
    private var cachedApiKey: String = ""

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

        // Show saved API key (masked by inputType="textPassword" in the layout).
        binding.editApiKey.setText(prefs.getString("elevenlabs_api_key", ""))

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

        binding.buttonSaveApiKey.setOnClickListener {
            val key = binding.editApiKey.text.toString().trim()
            prefs.edit().putString("elevenlabs_api_key", key).apply()
            Toast.makeText(requireContext(), "API key saved.", Toast.LENGTH_SHORT).show()
            checkQuota(key)
        }
    }

    // Automatically check the ElevenLabs quota whenever the settings tab is opened.
    override fun onResume() {
        super.onResume()
        val apiKey = requireContext()
            .getSharedPreferences("settings", Context.MODE_PRIVATE)
            .getString("elevenlabs_api_key", "") ?: ""
        checkQuota(apiKey)
    }

    private fun checkQuota(apiKey: String) {
        val quotaView = _binding?.textQuota ?: return
        if (apiKey.isBlank()) {
            quotaView.visibility = View.GONE
            return
        }

        // Reuse the client for the same key; recreate only when the key changes.
        if (elevenLabsClient == null || apiKey != cachedApiKey) {
            elevenLabsClient = ElevenLabsClient(apiKey)
            cachedApiKey = apiKey
        }

        elevenLabsClient!!.checkQuota(
            onResult = { used, limit ->
                activity?.runOnUiThread {
                    _binding?.textQuota?.apply {
                        text = "ElevenLabs quota: $used / $limit characters used"
                        visibility = View.VISIBLE
                    }
                }
            },
            onError = {
                activity?.runOnUiThread {
                    _binding?.textQuota?.apply {
                        text = "ElevenLabs quota: could not retrieve (check your API key)"
                        visibility = View.VISIBLE
                    }
                }
            }
        )
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
