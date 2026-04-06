package com.laufbanane2.hsklearning

import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject

data class UpdateInfo(val latestVersionCode: Int, val apkUrl: String)

object UpdateChecker {

    private const val RELEASES_URL =
        "https://api.github.com/repos/laufbanane2-create/hsk-learning/releases/latest"

    fun check(currentVersionCode: Int): UpdateInfo? {
        return try {
            val client = OkHttpClient()
            val request = Request.Builder()
                .url(RELEASES_URL)
                .header("Accept", "application/vnd.github+json")
                .build()
            val body = client.newCall(request).execute().use { it.body?.string() }
                ?: return null

            val json = JSONObject(body)
            val tagName = json.getString("tag_name")
            val latestVersionCode = tagName.removePrefix("v").toInt()

            if (latestVersionCode <= currentVersionCode) return null

            val apkUrl = json
                .getJSONArray("assets")
                .let { assets ->
                    (0 until assets.length())
                        .map { assets.getJSONObject(it) }
                        .firstOrNull { it.getString("name").endsWith(".apk") }
                        ?.getString("browser_download_url")
                } ?: return null

            UpdateInfo(latestVersionCode, apkUrl)
        } catch (_: Exception) {
            null
        }
    }
}
