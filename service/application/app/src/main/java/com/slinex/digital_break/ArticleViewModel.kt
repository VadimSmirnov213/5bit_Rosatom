package com.slinex.digital_break

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.slinex.digital_break.room.AppDatabaseInstance
import com.slinex.digital_break.room.Article
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class ArticleViewModel(application: Application) : AndroidViewModel(application) {
    private val articleDao = AppDatabaseInstance.getDatabase(application).articleDao()

    private val _articles = MutableStateFlow<List<Article>>(emptyList())
    val articles: StateFlow<List<Article>> = _articles.asStateFlow()

    init {
        // Collecting articles from the database to keep the UI updated
        viewModelScope.launch {
            articleDao.getAllArticles().collect {
                _articles.value = it
            }
        }
    }

    fun insertArticle(article: Article) {
        viewModelScope.launch {
            articleDao.insert(article)
        }
    }

//    fun getAllArticles(callback: (List<Article>) -> Unit) {
//        viewModelScope.launch {
//            callback(articleDao.getAllArticles())
//        }
//    }

    fun deleteArticle(article: Article) {
        viewModelScope.launch {
            articleDao.deleteArticle(article)
        }
    }

    fun updateArticle(article: Article) {
        viewModelScope.launch {
            articleDao.updateArticle(article)
        }
    }
}
