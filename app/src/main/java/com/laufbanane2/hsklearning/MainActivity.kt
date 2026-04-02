package com.laufbanane2.hsklearning

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import com.laufbanane2.hsklearning.databinding.ActivityMainBinding
import com.laufbanane2.hsklearning.ui.learn.LearnFragment
import com.laufbanane2.hsklearning.ui.settings.SettingsFragment

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        if (savedInstanceState == null) {
            showLearnFragment()
        }

        binding.bottomNavigation.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.nav_learn -> { showLearnFragment(); true }
                R.id.nav_settings -> { showSettingsFragment(); true }
                else -> false
            }
        }
    }

    private fun showLearnFragment() {
        supportFragmentManager.beginTransaction()
            .replace(R.id.fragmentContainer, LearnFragment())
            .commit()
    }

    private fun showSettingsFragment() {
        supportFragmentManager.beginTransaction()
            .replace(R.id.fragmentContainer, SettingsFragment())
            .commit()
    }
}
