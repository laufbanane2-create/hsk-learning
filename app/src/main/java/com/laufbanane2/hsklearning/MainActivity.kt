package com.laufbanane2.hsklearning

import android.content.Context
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.pm.PackageInfoCompat
import androidx.lifecycle.lifecycleScope
import com.laufbanane2.hsklearning.databinding.ActivityMainBinding
import com.laufbanane2.hsklearning.ui.learn.LearnFragment
import com.laufbanane2.hsklearning.ui.settings.SettingsFragment
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding

    companion object {
        private const val UPDATE_CHECK_INTERVAL_MS = 24 * 60 * 60 * 1000L // 24 hours
        private const val KEY_LAST_UPDATE_CHECK = "last_update_check_ms"
        private const val PREFS_SETTINGS = "settings"
    }

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

    override fun onResume() {
        super.onResume()
        maybeCheckForUpdate()
    }

    private fun maybeCheckForUpdate() {
        val prefs = getSharedPreferences(PREFS_SETTINGS, Context.MODE_PRIVATE)
        val lastCheck = prefs.getLong(KEY_LAST_UPDATE_CHECK, 0L)
        if (System.currentTimeMillis() - lastCheck < UPDATE_CHECK_INTERVAL_MS) return
        prefs.edit().putLong(KEY_LAST_UPDATE_CHECK, System.currentTimeMillis()).apply()
        checkForUpdate()
    }

    private fun checkForUpdate() {
        runUpdateCheck(showNoUpdateFeedback = false)
    }

    internal fun checkForUpdateManually() {
        runUpdateCheck(showNoUpdateFeedback = true)
    }

    private fun runUpdateCheck(showNoUpdateFeedback: Boolean) {
        val pkgInfo = packageManager.getPackageInfo(packageName, 0)
        val currentVersionCode = PackageInfoCompat.getLongVersionCode(pkgInfo).toInt()
        lifecycleScope.launch(Dispatchers.IO) {
            val updateInfo = UpdateChecker.check(currentVersionCode)
            withContext(Dispatchers.Main) {
                if (!isFinishing && !isDestroyed) {
                    if (updateInfo != null) {
                        AlertDialog.Builder(this@MainActivity)
                            .setTitle(getString(R.string.update_available_title))
                            .setMessage(getString(R.string.update_available_message))
                            .setPositiveButton(getString(R.string.update_action_now)) { _, _ ->
                                UpdateInstaller.downloadAndInstall(this@MainActivity, updateInfo.apkUrl)
                            }
                            .setNegativeButton(getString(R.string.update_action_later), null)
                            .show()
                    } else if (showNoUpdateFeedback) {
                        Toast.makeText(this@MainActivity, getString(R.string.update_up_to_date), Toast.LENGTH_SHORT).show()
                    }
                }
            }
        }
    }
}
