package com.slinex.digital_break.room

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "local_db")
data class Article(
    @PrimaryKey(autoGenerate = true)
    val id: Int = 0,
    val article: String,
    val number: String,
    val imagePath: String,
    val date: Long
)