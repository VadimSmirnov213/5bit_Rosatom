package com.slinex.digital_break

import android.Manifest
import android.annotation.SuppressLint
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.SystemBarStyle
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.TextFieldValue
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.FileProvider
import androidx.lifecycle.viewmodel.compose.viewModel
import coil.compose.rememberAsyncImagePainter
import com.slinex.digital_break.room.Article
import com.slinex.digital_break.ui.theme.DigitalBreakthroughTheme
import kotlinx.coroutines.launch
import java.io.File
import java.util.*

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        enableEdgeToEdge(
            statusBarStyle = SystemBarStyle.dark(scrim = Color.Transparent.toArgb())
        )



        setContent {
            var baseUrl by remember { mutableStateOf(TextFieldValue("http://192.144.12.43:8000/")) }

            DigitalBreakthroughTheme(darkTheme = true) {
                HomeScreen(
                    baseUrl = baseUrl,
                    sendPhoto = { uri ->
                        val apiService = ApiService.create(baseUrl = baseUrl.text)
                        uploadImage(apiService, uri, this)
                    },
                    onUrlValueChanged = {
                        baseUrl = it
                    }
                )
            }
        }
    }
}

@SuppressLint("UnrememberedMutableInteractionSource")
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    baseUrl: TextFieldValue,
    sendPhoto: suspend (uri: Uri) -> ApiResponse,
    onUrlValueChanged: (url: TextFieldValue) -> Unit
) {
    val coroutineScope = rememberCoroutineScope()
    var selectedImageUri by remember { mutableStateOf<Uri?>(null) }
    var photoUri by remember { mutableStateOf<Uri?>(null) }
    var isImageUploaded by remember { mutableStateOf(false) }
    var isLoading by remember { mutableStateOf(false) }
    var responseStatus by remember { mutableStateOf<String?>(null) }
    var responseArticle by remember { mutableStateOf<String?>(null) }
    var responseNumber by remember { mutableStateOf<String?>(null) }
    var responseMessage by remember { mutableStateOf<String?>(null) }
    var showDialog by remember { mutableStateOf(false) }
    var articleInEdit by remember { mutableStateOf<Article?>(null) }
    var showSettings by remember { mutableStateOf(false) }

    val context = LocalContext.current

    val imagePickerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent(),
        onResult = { uri -> selectedImageUri = uri }
    )

    val takePictureLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.TakePicture(),
        onResult = { success ->
            if (success) {
                selectedImageUri = photoUri
            } else {
                responseMessage = "Ошибка. Не удалось сделать фото."
            }
        }
    )

    val cameraPermissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission(),
        onResult = { isGranted ->
            if (isGranted) {
                photoUri?.let { takePictureLauncher.launch(it) }
            } else {
                responseMessage = "Необходим доступ к камере телефона"
            }
        }
    )

    val snackbarHostState = remember { SnackbarHostState() }
    var articleValue by remember { mutableStateOf(responseArticle ?: "") }
    var numberValue by remember { mutableStateOf("") }
    val focusManager = LocalFocusManager.current

    LaunchedEffect(selectedImageUri, photoUri) {
        isImageUploaded = selectedImageUri != null || photoUri != null
    }
    LaunchedEffect(responseMessage) {
        snackbarHostState.showSnackbar(
            message = responseMessage ?: "Ошибка",
        )
    }

    LaunchedEffect(responseArticle, responseNumber, responseStatus) {
        articleValue = responseArticle ?: ""
        numberValue = responseNumber ?: ""
    }

    val articleViewModel: ArticleViewModel = viewModel()

    val articles by articleViewModel.articles.collectAsState()  // Observe articles StateFlow
//    val (articles, setArticles) = remember { mutableStateOf(emptyList<Article>()) }
//
//    LaunchedEffect(Unit) {
//        articleViewModel.getAllArticles {
//            setArticles(it)
//        }
//    }

    var hasPermission by remember { mutableStateOf(false) }

    // Launcher to request permission
    val permissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        hasPermission = isGranted
        if (isGranted) {
            Toast.makeText(context, "Storage permission granted", Toast.LENGTH_SHORT).show()
//            onPermissionGranted()
        } else {
            Toast.makeText(context, "Storage permission denied", Toast.LENGTH_SHORT).show()
        }
    }

    // Check and request permission
    LaunchedEffect(Unit) {
        hasPermission = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            // From Android 13, the permission changes to READ_MEDIA_IMAGES
            context.checkSelfPermission(Manifest.permission.READ_MEDIA_IMAGES) == PackageManager.PERMISSION_GRANTED
        } else {
            // For Android 12 and below, use READ_EXTERNAL_STORAGE
            context.checkSelfPermission(Manifest.permission.READ_EXTERNAL_STORAGE) == PackageManager.PERMISSION_GRANTED
        }

        if (!hasPermission) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                permissionLauncher.launch(Manifest.permission.READ_MEDIA_IMAGES)
            } else {
                permissionLauncher.launch(Manifest.permission.READ_EXTERNAL_STORAGE)
            }
        }
    }

    val historyState = rememberLazyListState()

    Scaffold(
        modifier = Modifier.fillMaxSize(),
        containerColor = Color.Black,
        topBar = {
            CenterAlignedTopAppBar(
                colors = TopAppBarDefaults.centerAlignedTopAppBarColors(
                    containerColor = Color.Transparent,
                    titleContentColor = Color.White
                ),
                title = { Text("Загрузите картинку") },
                actions = {
                    IconButton(
                        onClick = {
                            showSettings = true
                        }
                    ) {
                        Icon(
                            painter = painterResource(R.drawable.ic_settings),
                            contentDescription = null,
                            modifier = Modifier.size(24.dp),
                            tint = Color.White
                        )
                    }
                }
            )
        }
    ) { innerPadding ->


        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(innerPadding)
                .fillMaxSize()
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.padding(horizontal = 16.dp)
            ) {
                selectedImageUri?.let { uri ->
                    Surface(
                        border = BorderStroke(1.dp, Color.Gray),
                        shape = RoundedCornerShape(16.dp),
                        color = Color.Transparent,
                        modifier = Modifier
                            .width(200.dp)
                            .height(150.dp)
                    ) {
                        Image(
                            painter = rememberAsyncImagePainter(model = uri),
                            contentDescription = "Выберите картинку",
                            modifier = Modifier
                                .width(200.dp)
                                .height(150.dp),
                            contentScale = ContentScale.Crop
                        )
                    }
                } ?: Surface(
                    border = BorderStroke(1.dp, Color.Gray),
                    shape = RoundedCornerShape(16.dp),
                    color = Color.Transparent,
                    modifier = Modifier
                        .width(200.dp)
                        .height(150.dp)
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Icon(
                            painter = painterResource(R.drawable.ic_image),
                            contentDescription = null,
                            modifier = Modifier.size(64.dp),
                            tint = Color.Gray
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "Не выбрано",
                            color = Color.Gray,
                            modifier = Modifier.padding(8.dp)
                        )
                    }
                }
                Spacer(Modifier.width(8.dp))
                Image(
                    painter = painterResource(R.drawable.img_9387_removebg_preview),
                    contentDescription = null
                )
            }
            Column(
                modifier = Modifier.padding(horizontal = 16.dp)
            ) {
                Spacer(modifier = Modifier.height(16.dp))

                Button(
                    modifier = Modifier.fillMaxWidth(),
                    onClick = {
                        if (isImageUploaded) {
                            showDialog = true
                            coroutineScope.launch {
                                isLoading = true
                                try {
                                    val response = sendPhoto(selectedImageUri!!)
                                    responseStatus = response.status
                                    responseArticle = response.article
                                    responseNumber = response.number
                                } catch (e: Exception) {
                                    responseMessage = e.message
                                    responseStatus = "null"
                                    responseArticle = "null"
                                    responseNumber = "null"
                                } finally {
                                    isLoading = false
                                }
                            }
                        } else {
                            imagePickerLauncher.launch("image/*")
                        }
                    },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(27, 58, 97),
                        contentColor = Color.White
                    )
                ) {
                    if (!isImageUploaded) {
                        Icon(
                            painter = painterResource(if (isImageUploaded) R.drawable.ic_send else R.drawable.ic_image),
                            contentDescription = null,
                            modifier = Modifier.size(24.dp),
                            tint = Color.White
                        )
                    }
                    Spacer(modifier = Modifier.size(8.dp))
                    Text(if (isImageUploaded) "Отправить" else "Выбрать", fontSize = 16.sp)
                    Spacer(modifier = Modifier.size(8.dp))
                    if (isImageUploaded) {
                        Icon(
                            painter = painterResource(if (isImageUploaded) R.drawable.ic_send else R.drawable.ic_image),
                            contentDescription = null,
                            modifier = Modifier.size(24.dp),
                            tint = Color.White
                        )
                    }
                }

                Button(
                    modifier = Modifier.fillMaxWidth(),
                    onClick = {
                        if (isImageUploaded) {
                            selectedImageUri = null
                            photoUri = null
                            responseMessage = ""
                        } else {
                            val photoFile = File(context.cacheDir, "${UUID.randomUUID()}.jpg")
                            photoUri = FileProvider.getUriForFile(
                                context,
                                "${context.packageName}.provider",
                                photoFile
                            )
                            cameraPermissionLauncher.launch(Manifest.permission.CAMERA)
                        }
                    },
                    border = BorderStroke(1.dp, Color(38, 85, 28)),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (isImageUploaded) Color.Transparent else Color(
                            38,
                            85,
                            28
                        ),
                        contentColor = if (isImageUploaded) Color(38, 85, 28) else Color.White,
                    )
                ) {
                    Icon(
                        painter = painterResource(if (isImageUploaded) R.drawable.ic_delete else R.drawable.ic_photo_camera),
                        contentDescription = null,
                        modifier = Modifier.size(24.dp),
                        tint = if (isImageUploaded) Color(38, 85, 28) else Color.White
                    )
                    Spacer(modifier = Modifier.size(8.dp))
                    Text(if (isImageUploaded) "Удалить" else "Сделать фото", fontSize = 16.sp)
                }
            }
            Spacer(Modifier.height(16.dp))
            HorizontalDivider()
            Spacer(Modifier.height(16.dp))
            Text(
                "История",
                fontSize = 24.sp,
                fontWeight = FontWeight.Medium,
                color = Color.White,
                modifier = Modifier.padding(horizontal = 16.dp)
            )
            Spacer(Modifier.height(16.dp))
            LazyColumn(
                modifier = Modifier
                    .padding(horizontal = 16.dp)
                    .weight(1f),
                state = historyState
            ) {
                items(articles.sortedBy { -it.date }) { article ->
                    ArticleListItem(
                        article,
                        onEditItem = {
                            showDialog = true
                            articleInEdit = article
                            articleValue = article.article
                            numberValue = article.number
                        },
                        onDeleteItem = {
                            articleViewModel.deleteArticle(article)
                        }
                    )
                }
            }
        }
    }




    if (showDialog) {
        AlertDialog(
            modifier = Modifier
                .clickable(interactionSource = MutableInteractionSource(), indication = null) {
                    focusManager.clearFocus(true)
                },
            onDismissRequest = { showDialog = false },
            confirmButton = {
                if (!isLoading) {
                    Button(
                        onClick = {
                            if (articleInEdit != null) {
                                articleViewModel.updateArticle(
                                    articleInEdit!!.copy(
                                        article = articleValue,
                                        number = numberValue
                                    )
                                )
                            } else {
                                articleViewModel.insertArticle(
                                    Article(
                                        article = articleValue,
                                        number = numberValue,
                                        imagePath = (selectedImageUri ?: photoUri ?: "").toString(),
                                        date = System.currentTimeMillis()
                                    )
                                )
                            }
                            showDialog = false
                            articleInEdit = null
                        }
                    ) {
                        Text("Сохранить")
                    }
                }
            },
            title = { Text(if (isLoading) "Анализ изображения" else if (articleInEdit != null) "Редактировать" else "Результат") },
            text = {
                if (isLoading) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.fillMaxWidth()) {
                        CircularProgressIndicator(
                            strokeCap = StrokeCap.Round,
                            strokeWidth = 3.dp
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        Text("Пожалуйста, подождите", fontSize = 16.sp)
                    }
                } else {
                    Column(horizontalAlignment = Alignment.Start) {

                        if (articleInEdit == null) Text("Статус: ${responseStatus ?: "N/A"}")
                        Spacer(modifier = Modifier.height(8.dp))
                        OutlinedTextField(
                            value = articleValue,
                            onValueChange = {
                                articleValue = it
                            },
                            label = {
                                Text("Артикул")
                            },
                            placeholder = {
                                Text("000-00-000")
                            },
                            shape = RoundedCornerShape(12.dp)
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        OutlinedTextField(
                            value = numberValue,
                            onValueChange = {
                                numberValue = it
                            },
                            label = {
                                Text("Номер")
                            },
                            placeholder = {
                                Text("00")
                            },
                            shape = RoundedCornerShape(12.dp)
                        )
                    }
                }
            }
        )
    }


    if (showSettings) {
        AlertDialog(
            onDismissRequest = {
                showSettings = false
            },
            title = {
                Text("Настройки")
            },
            text = {
                TextField(
                    value = baseUrl,
                    onValueChange = {
                        onUrlValueChanged(it)
                    },
                    colors = TextFieldDefaults.colors(
                        focusedContainerColor = Color.Transparent,
                        unfocusedContainerColor = Color.Transparent
                    )
                )
            },
            confirmButton = {
                Button(
                    onClick = {
                        showSettings = false
                    }
                ) {
                    Text("Сохранить")
                }
            }
        )
    }
}

@Composable
fun ArticleListItem(article: Article, onEditItem: () -> Unit, onDeleteItem: () -> Unit) {

    var selectedImageUri by remember { mutableStateOf<Uri?>(null) }
    val context = LocalContext.current

    val openDocumentLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocument()
    ) { uri ->
        if (uri != null) {
            context.contentResolver.takePersistableUriPermission(
                uri,
                Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION
            )
            selectedImageUri = uri // Store the URI for later use
        }
    }

    LaunchedEffect(Unit) {
//        openDocumentLauncher.launch(arrayOf(article.imagePath))

    }

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(bottom = 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box {
            Card(
                shape = RoundedCornerShape(8.dp),
                modifier = Modifier.size(48.dp),
                colors = CardDefaults.cardColors(containerColor = Color.Transparent)
            ) {
                Icon(
                    painter = painterResource(R.drawable.ic_image),
                    contentDescription = null,
                    tint = Color.Gray,
                    modifier = Modifier.size(48.dp)
                )
            }
            Image(
                painter = rememberAsyncImagePainter(
                    model = Uri.parse(article.imagePath),
//                    error = painterResource(R.drawable.ic_launcher_background),
                    onError = {
                        Log.d(
                            "img_loading_error",
                            "Error loading image: ${it.result.throwable.message}"
                        )
                    }
                ),
                contentDescription = null,
                modifier = Modifier
                    .width(48.dp)
                    .height(48.dp)
                    .clip(RoundedCornerShape(8.dp)),
                contentScale = ContentScale.Crop,
            )
        }
        Spacer(Modifier.width(16.dp))
        Column(
            modifier = Modifier
//                .height(48.dp)
                .weight(1f)
        ) {
            Row {
                Text(
                    "Артикул: ",
                    fontWeight = FontWeight.SemiBold,
                    color = Color.White
                )
                Text(
                    article.article,
                    color = Color.White,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
            }
            Row {
                Text(
                    "Номер: ",
                    fontWeight = FontWeight.SemiBold,
                    color = Color.White
                )
                Text(
                    article.number,
                    color = Color.White,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
            }
        }
        Spacer(Modifier.width(16.dp))
        IconButton(
            onClick = {
                onEditItem()
            }
        ) {
            Icon(
                painter = painterResource(R.drawable.ic_edit),
                contentDescription = null,
                modifier = Modifier.size(24.dp),
                tint = Color.White
            )
        }
        Spacer(Modifier.width(0.dp))
        IconButton(
            onClick = {
                onDeleteItem()
            }
        ) {
            Icon(
                painter = painterResource(R.drawable.ic_delete),
                contentDescription = null,
                modifier = Modifier.size(24.dp),
                tint = Color.White
            )
        }
    }
}