package com.laufbanane2.hsklearning.data

import okhttp3.Call
import okhttp3.Callback
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import org.json.JSONObject
import java.io.IOException

class ElevenLabsClient(private val apiKey: String) {

    private val client = OkHttpClient()

    // Adam voice — supports eleven_multilingual_v2 (Chinese included)
    private val voiceId = "pNInz6obpgDQGcFmaJgB"

    fun generateSpeech(text: String, onAudioBytes: (ByteArray) -> Unit, onError: () -> Unit) {
        if (apiKey.isBlank()) { onError(); return }

        val bodyJson = JSONObject().apply {
            put("text", text)
            put("model_id", "eleven_multilingual_v2")
            put("voice_settings", JSONObject().apply {
                put("stability", 0.5)
                put("similarity_boost", 0.75)
            })
        }.toString()

        val request = Request.Builder()
            .url("https://api.elevenlabs.io/v1/text-to-speech/$voiceId")
            .addHeader("xi-api-key", apiKey)
            .addHeader("Accept", "audio/mpeg")
            .post(bodyJson.toRequestBody("application/json".toMediaType()))
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) { onError() }
            override fun onResponse(call: Call, response: Response) {
                response.use {
                    if (it.isSuccessful) {
                        it.body?.bytes()?.let { bytes -> onAudioBytes(bytes) } ?: onError()
                    } else {
                        onError()
                    }
                }
            }
        })
    }

    fun checkQuota(onResult: (used: Int, limit: Int) -> Unit, onError: () -> Unit) {
        if (apiKey.isBlank()) { onError(); return }

        val request = Request.Builder()
            .url("https://api.elevenlabs.io/v1/user/subscription")
            .addHeader("xi-api-key", apiKey)
            .get()
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) { onError() }
            override fun onResponse(call: Call, response: Response) {
                response.use {
                    if (it.isSuccessful) {
                        try {
                            val json = JSONObject(it.body?.string() ?: "")
                            val used = json.getInt("character_count")
                            val limit = json.getInt("character_limit")
                            onResult(used, limit)
                        } catch (e: Exception) {
                            onError()
                        }
                    } else {
                        onError()
                    }
                }
            }
        })
    }
}
