package com.slinex.digital_break.room

import android.content.Context
import androidx.room.Room

object AppDatabaseInstance {
    @Volatile
    private var INSTANCE: AppDatabase? = null

    fun getDatabase(context: Context): AppDatabase {
        return INSTANCE ?: synchronized(this) {
            val instance = Room.databaseBuilder(
                context.applicationContext,
                AppDatabase::class.java,
                "local_db"
            ).build()
            INSTANCE = instance
            instance
        }
    }
}