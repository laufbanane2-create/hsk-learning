package com.laufbanane2.hsklearning

import android.util.Log
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONArray

data class UpdateInfo(val latestVersionCode: Int, val apkUrl: String)

object UpdateChecker {

    private const val RELEASES_URL =
        "https://api.github.com/repos/laufbanane2-create/hsk-learning/releases"

    fun check(currentVersionCode: Int): UpdateInfo? {
        return try {
            val client = OkHttpClient()
            val request = Request.Builder()
                .url(RELEASES_URL)
                .header("Accept", "application/vnd.github+json")
                .build()
            val body = client.newCall(request).execute().use { it.body?.string() }
                ?: return null

            val releases = JSONArray(body)

            // Find the release with the highest version code (includes prereleases).
            var bestVersionCode = currentVersionCode
            var bestApkUrl: String? = null

            for (i in 0 until releases.length()) {
                val json = releases.getJSONObject(i)
                val tagName = json.optString("tag_name").takeIf { it.isNotEmpty() } ?: continue
                val versionCode = tagName.removePrefix("v").toIntOrNull() ?: continue
                if (versionCode <= bestVersionCode) continue

                val apkUrl = json
                    .getJSONArray("assets")
                    .let { assets ->
                        (0 until assets.length())
                            .map { assets.getJSONObject(it) }
                            .firstOrNull { it.getString("name").endsWith(".apk") }
                            ?.getString("browser_download_url")
                    } ?: continue

                bestVersionCode = versionCode
                bestApkUrl = apkUrl
            }

            if (bestApkUrl == null) return null
            UpdateInfo(bestVersionCode, bestApkUrl)
        } catch (e: Exception) {
            Log.w("UpdateChecker", "Update check failed", e)
            null
        }
    }
}
