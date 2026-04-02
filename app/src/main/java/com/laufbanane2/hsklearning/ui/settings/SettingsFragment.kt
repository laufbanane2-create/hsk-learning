package com.laufbanane2.hsklearning.ui.settings

import android.content.Context
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
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
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
