package com.slinex.digital_break

import android.content.Context
import android.net.Uri
import android.util.Log
import androidx.core.net.toFile
import com.google.gson.Gson
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.HttpException
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part
import java.io.File
import java.io.FileOutputStream
import java.io.IOException
import java.io.InputStream

interface ApiService {
    @Multipart
    @POST("/api/process_image")
    suspend fun uploadImage(@Part file: MultipartBody.Part): ApiResponse

    companion object {
        private const val BASE_URL = "http://192.144.12.43:8000/"

        fun create(baseUrl: String = BASE_URL): ApiService {
            val logging = HttpLoggingInterceptor().apply { level = HttpLoggingInterceptor.Level.BODY }
            val client = OkHttpClient.Builder().addInterceptor(logging).build()

            return Retrofit.Builder()
                .baseUrl(baseUrl)
                .client(client)
                .addConverterFactory(GsonConverterFactory.create())
                .build()
                .create(ApiService::class.java)
        }
    }
}


suspend fun uploadImage(apiService: ApiService, uri: Uri, context: Context): ApiResponse {
    val file = createFileFromContentUri(uri, context)
    val requestFile = file.asRequestBody("image/*".toMediaTypeOrNull())
    val body = MultipartBody.Part.createFormData("file", file.name, requestFile)

    return try {
        apiService.uploadImage(body)
    } catch (e: HttpException) {
        if (e.code() == 422) {
            // Parse validation error
            val errorBody = e.response()?.errorBody()?.string()
            val validationError = Gson().fromJson(errorBody, ValidationError::class.java)
            throw Exception("Validation Error: ${validationError.detail.joinToString { it.msg }}")
        } else {
            throw e
        }
    } catch (e: IOException) {
        throw Exception("Network error: ${e.message}")
    }
}

fun createFileFromContentUri(contentUri: Uri, context: Context): File {
    val fileName = "temp_image_file.jpg"
    val tempFile = File(context.cacheDir, fileName)
    tempFile.createNewFile()

    val inputStream: InputStream? = context.contentResolver.openInputStream(contentUri)
    val outputStream = FileOutputStream(tempFile)

    inputStream?.use { input ->
        outputStream.use { output ->
            input.copyTo(output)
        }
    }

    return tempFile
}


data class ApiResponse(
    val status: String,
    val article: String,
    val number: String
)

data class ValidationError(
    val detail: List<ValidationErrorDetail>
)

data class ValidationErrorDetail(
    val loc: List<Any>,
    val msg: String,
    val type: String
)
