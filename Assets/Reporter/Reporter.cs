#if UNITY_CHANGE1 || UNITY_CHANGE2 || UNITY_CHANGE3 || UNITY_CHANGE4
#warning UNITY_CHANGE has been set manually
#elif UNITY_4_0 || UNITY_4_1 || UNITY_4_2 || UNITY_4_3 || UNITY_4_4 || UNITY_4_5 || UNITY_4_6 || UNITY_4_7
#define UNITY_CHANGE1
#elif UNITY_5_0 || UNITY_5_1 || UNITY_5_2
#define UNITY_CHANGE2
#else
#define UNITY_CHANGE3
#endif
#if UNITY_2018_3_OR_NEWER
#define UNITY_CHANGE4
#endif
//use UNITY_CHANGE1 for unity older than "unity 5"
//use UNITY_CHANGE2 for unity 5.0 -> 5.3 
//use UNITY_CHANGE3 for unity 5.3 (fix for new SceneManger system)
//use UNITY_CHANGE4 for unity 2018.3 (Networking system)

using UnityEngine;
using System.IO;
using System.Collections;
using System.Collections.Generic;
#if UNITY_CHANGE3
using UnityEngine.SceneManagement;
#endif
#if UNITY_CHANGE4
using UnityEngine.Networking;
#endif


[System.Serializable]
public class Images
{
	public Texture2D clearImage;
	public Texture2D collapseImage;
	public Texture2D clearOnNewSceneImage;
	public Texture2D showTimeImage;
	public Texture2D showSceneImage;
	public Texture2D userImage;
	public Texture2D showMemoryImage;
	public Texture2D softwareImage;
	public Texture2D dateImage;
	public Texture2D showFpsImage;
	public Texture2D infoImage;
    public Texture2D saveLogsImage; 
    public Texture2D searchImage;
    public Texture2D copyImage;
    public Texture2D copyAllImage;
    public Texture2D closeImage;

	public Texture2D buildFromImage;
	public Texture2D systemInfoImage;
	public Texture2D graphicsInfoImage;
	public Texture2D backImage;

	public Texture2D logImage;
	public Texture2D warningImage;
	public Texture2D errorImage;

	public Texture2D barImage;
	public Texture2D button_activeImage;
	public Texture2D even_logImage;
	public Texture2D odd_logImage;
	public Texture2D selectedImage;

	public GUISkin reporterScrollerSkin;
}

//To use Reporter just create reporter from menu (Reporter->Create) at first scene your game start.
//then set the ” Scrip execution order ” in (Edit -> Project Settings ) of Reporter.cs to be the highest.

//Now to view logs all what you have to do is to make a circle gesture using your mouse (click and drag) 
//or your finger (touch and drag) on the screen to show all these logs
//no coding is required 

public class Reporter : MonoBehaviour
{

	public enum _LogType
	{
		Assert    = LogType.Assert,
		Error     = LogType.Error,
		Exception = LogType.Exception,
		Log       = LogType.Log,
		Warning   = LogType.Warning,
	}

	public class Sample
	{
		public float time;
		public byte loadedScene;
		public float memory;
		public float fps;
		public string fpsText;
		public static float MemSize()
		{
			float s = sizeof(float) + sizeof(byte) + sizeof(float) + sizeof(float);
			return s;
		}

		public string GetSceneName()
		{
			if (loadedScene == 255)
				return "AssetBundleScene";

			return scenes[loadedScene];
		}
	}

	List<Sample> samples = new List<Sample>();

	public class Log
	{
		public int count = 1;
		public _LogType logType;
		public string condition;
		public string stacktrace;
		public int sampleId;
		//public string   objectName="" ;//object who send error
		//public string   rootName =""; //root of object send error

		public Log CreateCopy()
		{
			return (Log)this.MemberwiseClone();
		}
		public float GetMemoryUsage()
		{
			return (float)(sizeof(int) +
					sizeof(_LogType) +
					condition.Length * sizeof(char) +
					stacktrace.Length * sizeof(char) +
					sizeof(int));
		}
	}
	//contains all uncollapsed log
	List<Log> logs = new List<Log>();
	//contains all collapsed logs
	List<Log> collapsedLogs = new List<Log>();
	//contain logs which should only appear to user , for example if you switch off show logs + switch off show warnings
	//and your mode is collapse,then this list will contains only collapsed errors
	List<Log> currentLog = new List<Log>();

	//used to check if the new coming logs is already exist or new one
	MultiKeyDictionary<string, string, Log> logsDic = new MultiKeyDictionary<string, string, Log>();
	//to save memory
	Dictionary<string, string> cachedString = new Dictionary<string, string>();

	[HideInInspector]
	//show hide In Game Logs
	public bool show = false;
	//collapse logs
	bool collapse;
	//to decide if you want to clean logs for new loaded scene
	bool clearOnNewSceneLoaded;

	bool showTime;

	bool showScene;

	bool showMemory;

	bool showFps;

	bool showGraph;

	//show or hide logs
	bool showLog = true;
	//show or hide warnings
	bool showWarning = true;
	//show or hide errors
	bool showError = true;

	//total number of logs
	int numOfLogs = 0;
	//total number of warnings
	int numOfLogsWarning = 0;
	//total number of errors
	int numOfLogsError = 0;
	//total number of collapsed logs
	int numOfCollapsedLogs = 0;
	//total number of collapsed warnings
	int numOfCollapsedLogsWarning = 0;
	//total number of collapsed errors
	int numOfCollapsedLogsError = 0;

	//maximum number of allowed logs to view
	//public int maxAllowedLog = 1000 ;

	bool showClearOnNewSceneLoadedButton = true;
	bool showTimeButton = true;
	bool showSceneButton = true;
	bool showMemButton = true;
	bool showFpsButton = true;
	bool showSearchText = true;
    bool showCopyButton = true;
    bool showCopyAllButton = true;
    bool showSaveButton = true;

    string buildDate;
	string logDate;
	float logsMemUsage;
	float graphMemUsage;
	public float TotalMemUsage
	{
		get
		{
			return logsMemUsage + graphMemUsage;
		}
	}
	float gcTotalMemory;
	public string UserData = "";
	//frame rate per second
	public float fps;
	public string fpsText;

	//List<Texture2D> snapshots = new List<Texture2D>() ;

	enum ReportView
	{
		None,
		Logs,
		Info,
		Snapshot,
	}
	ReportView currentView = ReportView.Logs;
	enum DetailView
	{
		None,
		StackTrace,
		Graph,
	}

	//used to check if you have In Game Logs multiple time in different scene
	//only one should work and other should be deleted
	static bool created = false;
	//public delegate void OnLogHandler( string condition, string stack-trace, LogType type );
	//public event OnLogHandler OnLog ;

	public Images images;

	// ------------------------------------------------------------------
	// 【运行时图片加载钩子 —— 动态挂载专用】
	//
	// 原版工作流：编辑器菜单「Reporter/Create」创建物体时把 Assets/Reporter/Images/*
	// 填进 images 并随场景序列化。本工程改为**运行时 AddComponent**（HybridCLR 限制：
	// 挂热更脚本的物体不能进场景/Resources），序列化路径完全不经过 → images 为 null，
	// Initialize 里一取 images.xxx 就 NullReferenceException：初始化中断（Initialized
	// 停在 false）、GUI 资源全空，表现就是"画圈/双击都没反应、面板永远打不开"。
	//
	// 由调用方（GameSceneLauncher.EnsureReporter）注入加载器：图片走工程统一资源链路
	// （编辑器 AssetDatabase / 真机 YooAsset AB，ResTable 逻辑名 Reporter_<文件>）；
	// 未注入或加载失败时自动退化为程序化占位贴图与空 GUISkin ——
	// **保证 Initialize 在任何路径上都不崩**。
	// ------------------------------------------------------------------
	public static System.Func<string, Texture2D> ImageLoader;
	public static System.Func<GUISkin> ScrollerSkinLoader;

	/// <summary>当前存活实例（跨场景重载守卫用；Unity 伪 null 语义下销毁后自动为空）。</summary>
	public static Reporter Instance;

	// gui
	GUIContent clearContent;
	GUIContent collapseContent;
	GUIContent clearOnNewSceneContent;
	GUIContent showTimeContent;
	GUIContent showSceneContent;
	GUIContent userContent;
	GUIContent showMemoryContent;
	GUIContent softwareContent;
	GUIContent dateContent;
	GUIContent showFpsContent;
	//GUIContent graphContent;
	GUIContent infoContent;
    GUIContent saveLogsContent;
	GUIContent searchContent;
    GUIContent copyContent;
    GUIContent copyAllContent;
    GUIContent closeContent;

	GUIContent buildFromContent;
	GUIContent systemInfoContent;
	GUIContent graphicsInfoContent;
	GUIContent backContent;

	//GUIContent cameraContent;

	GUIContent logContent;
	GUIContent warningContent;
	GUIContent errorContent;
	GUIStyle barStyle;
	GUIStyle buttonActiveStyle;

	GUIStyle nonStyle;
	GUIStyle lowerLeftFontStyle;
	GUIStyle backStyle;
	GUIStyle evenLogStyle;
	GUIStyle oddLogStyle;
	GUIStyle logButtonStyle;
	GUIStyle selectedLogStyle;
	GUIStyle selectedLogFontStyle;
	GUIStyle stackLabelStyle;
	GUIStyle scrollerStyle;
	GUIStyle searchStyle;
	GUIStyle sliderBackStyle;
	GUIStyle sliderThumbStyle;
	GUISkin toolbarScrollerSkin;
	GUISkin logScrollerSkin;
	GUISkin graphScrollerSkin;

	public Vector2 size = new Vector2(32, 32);
	public float maxSize = 20;
	public int numOfCircleToShow = 1;
	static string[] scenes;
	string currentScene;
	string filterText = "";

	string deviceModel;
	string deviceType;
	string deviceName;
	string graphicsMemorySize;
#if !UNITY_CHANGE1
	string maxTextureSize;
#endif
	string systemMemorySize;

	void Awake()
	{
		if (!Initialized)
			Initialize();

#if UNITY_CHANGE3
        SceneManager.sceneLoaded += _OnLevelWasLoaded;
#endif
    }

    private void OnDestroy()
    {
#if UNITY_CHANGE3
        SceneManager.sceneLoaded -= _OnLevelWasLoaded;
#endif
    }

    void OnEnable()
	{
		if (logs.Count == 0)//if recompile while in play mode
			clear();
	}

	void OnDisable()
	{

	}

	void addSample()
	{
		Sample sample = new Sample();
		sample.fps = fps;
		sample.fpsText = fpsText;
#if UNITY_CHANGE3
		sample.loadedScene = (byte)SceneManager.GetActiveScene().buildIndex;
#else
		sample.loadedScene = (byte)Application.loadedLevel;
#endif
		sample.time = Time.realtimeSinceStartup;
		sample.memory = gcTotalMemory;
		samples.Add(sample);

		graphMemUsage = (samples.Count * Sample.MemSize()) / 1024 / 1024;
	}

	// ------------------------------------------------------------------
	// 【运行时图片装配】动态挂载路径专用（见 ImageLoader 字段区说明）。
	//
	// 加载顺序：注入的 ImageLoader（真机=YooAsset / 编辑器=AssetDatabase 直读）
	//   → Resources 兜底（历史兼容路径，正常不命中）
	//   → 程序化占位贴图（半透明灰，保证 GUIContent / GUIStyle 引用非空）。
	// GUISkin 同理；加载失败时退化为空 GUISkin（滚动条无皮肤但功能正常）。
	// 映射名与 Assets/Reporter/Images/ 下文件名逐一对应，同时对齐 ResTable 的
	// Reporter_* 逻辑名与收集器目录 —— 三处改名必须同步。
	// ------------------------------------------------------------------
	private static Texture2D _placeholderTexture;

	private static Texture2D PlaceholderTexture
	{
		get
		{
			if (_placeholderTexture == null)
			{
				_placeholderTexture = new Texture2D(2, 2, TextureFormat.RGBA32, false);
				Color c = new Color(0.6f, 0.6f, 0.6f, 0.35f);
				_placeholderTexture.SetPixels(new[] { c, c, c, c });
				_placeholderTexture.Apply();
				_placeholderTexture.hideFlags = HideFlags.HideAndDontSave;
			}
			return _placeholderTexture;
		}
	}

	private static Texture2D LoadTextureSafe(string name)
	{
		Texture2D tex = null;
		if (ImageLoader != null)
		{
			try
			{
				tex = ImageLoader(name);
			}
			catch (System.Exception e)
			{
				Debug.LogWarning("[Reporter] 图片加载器异常（" + name + "）：" + e.Message);
			}
		}
		if (tex == null)
		{
			try
			{
				tex = Resources.Load<Texture2D>("Reporter/" + name);
			}
			catch (System.Exception)
			{
				// Resources 目录通常没有这些图，失败静默走占位 —— 不刷屏
			}
		}
		if (tex == null)
		{
			tex = PlaceholderTexture;
		}
		return tex;
	}

	private static GUISkin LoadSkinSafe()
	{
		GUISkin skin = null;
		if (ScrollerSkinLoader != null)
		{
			try
			{
				skin = ScrollerSkinLoader();
			}
			catch (System.Exception e)
			{
				Debug.LogWarning("[Reporter] GUISkin 加载器异常：" + e.Message);
			}
		}
		if (skin == null)
		{
			// 空 GUISkin：滚动条样式取默认值，功能不缺失。
			// 用非泛型 CreateInstance（HybridCLR 下泛型重载可能缺 AOT 实例化）。
			skin = ScriptableObject.CreateInstance(typeof(GUISkin)) as GUISkin;
			if (skin != null)
			{
				skin.hideFlags = HideFlags.HideAndDontSave;
			}
		}
		return skin;
	}

	private static Images CreateRuntimeImages()
	{
		Images img = new Images();
		img.clearImage = LoadTextureSafe("clear");
		img.collapseImage = LoadTextureSafe("collapse");
		img.clearOnNewSceneImage = LoadTextureSafe("clearOnSceneLoaded");
		img.showTimeImage = LoadTextureSafe("timer_1");
		img.showSceneImage = LoadTextureSafe("UnityIcon");
		img.userImage = LoadTextureSafe("user");
		img.showMemoryImage = LoadTextureSafe("memory");
		img.softwareImage = LoadTextureSafe("software");
		img.dateImage = LoadTextureSafe("date");
		img.showFpsImage = LoadTextureSafe("fps");
		img.infoImage = LoadTextureSafe("info");
		img.saveLogsImage = LoadTextureSafe("Save");
		img.searchImage = LoadTextureSafe("search");
		img.copyImage = LoadTextureSafe("copy");
		img.copyAllImage = LoadTextureSafe("copyAll");
		img.closeImage = LoadTextureSafe("close");
		img.buildFromImage = LoadTextureSafe("buildFrom");
		img.systemInfoImage = LoadTextureSafe("ComputerIcon");
		img.graphicsInfoImage = LoadTextureSafe("graphicCard");
		img.backImage = LoadTextureSafe("back");
		img.logImage = LoadTextureSafe("log_icon");
		img.warningImage = LoadTextureSafe("warning_icon");
		img.errorImage = LoadTextureSafe("error_icon");
		img.barImage = LoadTextureSafe("bar");
		img.button_activeImage = LoadTextureSafe("button_active");
		img.even_logImage = LoadTextureSafe("even_log");
		img.odd_logImage = LoadTextureSafe("odd_log");
		img.selectedImage = LoadTextureSafe("selected");
		img.reporterScrollerSkin = LoadSkinSafe();
		return img;
	}

	public bool Initialized = false;
	public void Initialize()
	{
		if (!created) {
			try {
				gameObject.SendMessage("OnPreStart");
			}
			catch (System.Exception e) {
				Debug.LogException(e);
			}
#if UNITY_CHANGE3
			scenes = new string[ SceneManager.sceneCountInBuildSettings ];
			currentScene = SceneManager.GetActiveScene().name;
#else
			scenes = new string[Application.levelCount];
			currentScene = Application.loadedLevelName;
#endif
			DontDestroyOnLoad(gameObject);
#if UNITY_CHANGE1
			Application.RegisterLogCallback (new Application.LogCallback (CaptureLog));
			Application.RegisterLogCallbackThreaded (new Application.LogCallback (CaptureLogThread));
#else
			//Application.logMessageReceived += CaptureLog ;
			Application.logMessageReceivedThreaded += CaptureLogThread;
#endif
			created = true;
			Instance = this;
			//addSample();
		}
		else {
			Debug.LogWarning("tow manager is exists delete the second");
			DestroyImmediate(gameObject, true);
			return;
		}


		//initialize gui and styles for gui purpose

		// 【运行时兜底装配】动态 AddComponent 路径没有序列化的 images（见字段区说明），
		// 这里现场装配；不清空直接复用（编辑器菜单创建过的资产路径保留原引用）。
		if (images == null || images.clearImage == null)
		{
			images = CreateRuntimeImages();
		}

		clearContent = new GUIContent("", images.clearImage, "Clear logs");
		collapseContent = new GUIContent("", images.collapseImage, "Collapse logs");
		clearOnNewSceneContent = new GUIContent("", images.clearOnNewSceneImage, "Clear logs on new scene loaded");
		showTimeContent = new GUIContent("", images.showTimeImage, "Show Hide Time");
		showSceneContent = new GUIContent("", images.showSceneImage, "Show Hide Scene");
		showMemoryContent = new GUIContent("", images.showMemoryImage, "Show Hide Memory");
		softwareContent = new GUIContent("", images.softwareImage, "Software");
		dateContent = new GUIContent("", images.dateImage, "Date");
		showFpsContent = new GUIContent("", images.showFpsImage, "Show Hide fps");
		infoContent = new GUIContent("", images.infoImage, "Information about application");
        saveLogsContent = new GUIContent("", images.saveLogsImage, "Save logs to device");
        searchContent = new GUIContent("", images.searchImage, "Search for logs");
        copyContent = new GUIContent("", images.copyImage, "Copy log to clipboard");
        copyAllContent = new GUIContent("", images.copyAllImage, "Copy all logs to clipboard");
        closeContent = new GUIContent("", images.closeImage, "Hide logs");
		userContent = new GUIContent("", images.userImage, "User");

		buildFromContent = new GUIContent("", images.buildFromImage, "Build From");
		systemInfoContent = new GUIContent("", images.systemInfoImage, "System Info");
		graphicsInfoContent = new GUIContent("", images.graphicsInfoImage, "Graphics Info");
		backContent = new GUIContent("", images.backImage, "Back");


		//snapshotContent = new GUIContent("",images.cameraImage,"show or hide logs");
		logContent = new GUIContent("", images.logImage, "show or hide logs");
		warningContent = new GUIContent("", images.warningImage, "show or hide warnings");
		errorContent = new GUIContent("", images.errorImage, "show or hide errors");


		currentView = (ReportView)PlayerPrefs.GetInt("Reporter_currentView", 1);
		show = (PlayerPrefs.GetInt("Reporter_show") == 1) ? true : false;
		collapse = (PlayerPrefs.GetInt("Reporter_collapse") == 1) ? true : false;
		clearOnNewSceneLoaded = (PlayerPrefs.GetInt("Reporter_clearOnNewSceneLoaded") == 1) ? true : false;
		showTime = (PlayerPrefs.GetInt("Reporter_showTime") == 1) ? true : false;
		showScene = (PlayerPrefs.GetInt("Reporter_showScene") == 1) ? true : false;
		showMemory = (PlayerPrefs.GetInt("Reporter_showMemory") == 1) ? true : false;
		showFps = (PlayerPrefs.GetInt("Reporter_showFps") == 1) ? true : false;
		showGraph = (PlayerPrefs.GetInt("Reporter_showGraph") == 1) ? true : false;
		showLog = (PlayerPrefs.GetInt("Reporter_showLog", 1) == 1) ? true : false;
		showWarning = (PlayerPrefs.GetInt("Reporter_showWarning", 1) == 1) ? true : false;
		showError = (PlayerPrefs.GetInt("Reporter_showError", 1) == 1) ? true : false;
		filterText = PlayerPrefs.GetString("Reporter_filterText");
		size.x = size.y = PlayerPrefs.GetFloat("Reporter_size", 32);


		showClearOnNewSceneLoadedButton = (PlayerPrefs.GetInt("Reporter_showClearOnNewSceneLoadedButton", 1) == 1) ? true : false;
		showTimeButton = (PlayerPrefs.GetInt("Reporter_showTimeButton", 1) == 1) ? true : false;
		showSceneButton = (PlayerPrefs.GetInt("Reporter_showSceneButton", 1) == 1) ? true : false;
		showMemButton = (PlayerPrefs.GetInt("Reporter_showMemButton", 1) == 1) ? true : false;
		showFpsButton = (PlayerPrefs.GetInt("Reporter_showFpsButton", 1) == 1) ? true : false;
		showSearchText = (PlayerPrefs.GetInt("Reporter_showSearchText", 1) == 1) ? true : false;
        showCopyButton = (PlayerPrefs.GetInt("Reporter_showCopyButton", 1) == 1) ? true : false;
        showCopyAllButton = (PlayerPrefs.GetInt("Reporter_showCopyAllButton", 1) == 1) ? true : false;
        showSaveButton = (PlayerPrefs.GetInt("Reporter_showSaveButton", 1) == 1) ? true : false;


        initializeStyle();

		Initialized = true;

		if (show) {
			doShow();
		}

		deviceModel = SystemInfo.deviceModel.ToString();
		deviceType = SystemInfo.deviceType.ToString();
		deviceName = SystemInfo.deviceName.ToString();
		graphicsMemorySize = SystemInfo.graphicsMemorySize.ToString();
#if !UNITY_CHANGE1
		maxTextureSize = SystemInfo.maxTextureSize.ToString();
#endif
		systemMemorySize = SystemInfo.systemMemorySize.ToString();

	}

	void initializeStyle()
	{
		int paddingX = (int)(size.x * 0.2f);
		int paddingY = (int)(size.y * 0.2f);
		nonStyle = new GUIStyle();
		nonStyle.clipping = TextClipping.Clip;
		nonStyle.border = new RectOffset(0, 0, 0, 0);
		nonStyle.normal.background = null;
		nonStyle.fontSize = (int)(size.y / 2);
		nonStyle.alignment = TextAnchor.MiddleCenter;

		lowerLeftFontStyle = new GUIStyle();
		lowerLeftFontStyle.clipping = TextClipping.Clip;
		lowerLeftFontStyle.border = new RectOffset(0, 0, 0, 0);
		lowerLeftFontStyle.normal.background = null;
		lowerLeftFontStyle.fontSize = (int)(size.y / 2);
		lowerLeftFontStyle.fontStyle = FontStyle.Bold;
		lowerLeftFontStyle.alignment = TextAnchor.LowerLeft;


		barStyle = new GUIStyle();
		barStyle.border = new RectOffset(1, 1, 1, 1);
		barStyle.normal.background = images.barImage;
		barStyle.active.background = images.button_activeImage;
		barStyle.alignment = TextAnchor.MiddleCenter;
		barStyle.margin = new RectOffset(1, 1, 1, 1);

		//barStyle.padding = new RectOffset(paddingX,paddingX,paddingY,paddingY); 
		//barStyle.wordWrap = true ;
		barStyle.clipping = TextClipping.Clip;
		barStyle.fontSize = (int)(size.y / 2);


		buttonActiveStyle = new GUIStyle();
		buttonActiveStyle.border = new RectOffset(1, 1, 1, 1);
		buttonActiveStyle.normal.background = images.button_activeImage;
		buttonActiveStyle.alignment = TextAnchor.MiddleCenter;
		buttonActiveStyle.margin = new RectOffset(1, 1, 1, 1);
		//buttonActiveStyle.padding = new RectOffset(4,4,4,4);
		buttonActiveStyle.fontSize = (int)(size.y / 2);

		backStyle = new GUIStyle();
		backStyle.normal.background = images.even_logImage;
		backStyle.clipping = TextClipping.Clip;
		backStyle.fontSize = (int)(size.y / 2);

		evenLogStyle = new GUIStyle();
		evenLogStyle.normal.background = images.even_logImage;
		evenLogStyle.fixedHeight = size.y;
		evenLogStyle.clipping = TextClipping.Clip;
		evenLogStyle.alignment = TextAnchor.UpperLeft;
		evenLogStyle.imagePosition = ImagePosition.ImageLeft;
		evenLogStyle.fontSize = (int)(size.y / 2);
		//evenLogStyle.wordWrap = true;

		oddLogStyle = new GUIStyle();
		oddLogStyle.normal.background = images.odd_logImage;
		oddLogStyle.fixedHeight = size.y;
		oddLogStyle.clipping = TextClipping.Clip;
		oddLogStyle.alignment = TextAnchor.UpperLeft;
		oddLogStyle.imagePosition = ImagePosition.ImageLeft;
		oddLogStyle.fontSize = (int)(size.y / 2);
		//oddLogStyle.wordWrap = true ;

		logButtonStyle = new GUIStyle();
		//logButtonStyle.wordWrap = true;
		logButtonStyle.fixedHeight = size.y;
		logButtonStyle.clipping = TextClipping.Clip;
		logButtonStyle.alignment = TextAnchor.UpperLeft;
		//logButtonStyle.imagePosition = ImagePosition.ImageLeft ;
		//logButtonStyle.wordWrap = true;
		logButtonStyle.fontSize = (int)(size.y / 2);
		logButtonStyle.padding = new RectOffset(paddingX, paddingX, paddingY, paddingY);

		selectedLogStyle = new GUIStyle();
		selectedLogStyle.normal.background = images.selectedImage;
		selectedLogStyle.fixedHeight = size.y;
		selectedLogStyle.clipping = TextClipping.Clip;
		selectedLogStyle.alignment = TextAnchor.UpperLeft;
		selectedLogStyle.normal.textColor = Color.white;
		//selectedLogStyle.wordWrap = true;
		selectedLogStyle.fontSize = (int)(size.y / 2);

		selectedLogFontStyle = new GUIStyle();
		selectedLogFontStyle.normal.background = images.selectedImage;
		selectedLogFontStyle.fixedHeight = size.y;
		selectedLogFontStyle.clipping = TextClipping.Clip;
		selectedLogFontStyle.alignment = TextAnchor.UpperLeft;
		selectedLogFontStyle.normal.textColor = Color.white;
		//selectedLogStyle.wordWrap = true;
		selectedLogFontStyle.fontSize = (int)(size.y / 2);
		selectedLogFontStyle.padding = new RectOffset(paddingX, paddingX, paddingY, paddingY);

		stackLabelStyle = new GUIStyle();
		stackLabelStyle.wordWrap = true;
		stackLabelStyle.fontSize = (int)(size.y / 2);
		stackLabelStyle.padding = new RectOffset(paddingX, paddingX, paddingY, paddingY);

		scrollerStyle = new GUIStyle();
		scrollerStyle.normal.background = images.barImage;

		searchStyle = new GUIStyle();
		searchStyle.clipping = TextClipping.Clip;
		searchStyle.alignment = TextAnchor.LowerCenter;
		searchStyle.fontSize = (int)(size.y / 2);
		searchStyle.wordWrap = true;


		sliderBackStyle = new GUIStyle();
		sliderBackStyle.normal.background = images.barImage;
		sliderBackStyle.fixedHeight = size.y;
		sliderBackStyle.border = new RectOffset(1, 1, 1, 1);

		sliderThumbStyle = new GUIStyle();
		sliderThumbStyle.normal.background = images.selectedImage;
		sliderThumbStyle.fixedWidth = size.x;

		GUISkin skin = images.reporterScrollerSkin;

		toolbarScrollerSkin = (GUISkin)GameObject.Instantiate(skin);
		toolbarScrollerSkin.verticalScrollbar.fixedWidth = 0f;
		toolbarScrollerSkin.horizontalScrollbar.fixedHeight = 0f;
		toolbarScrollerSkin.verticalScrollbarThumb.fixedWidth = 0f;
		toolbarScrollerSkin.horizontalScrollbarThumb.fixedHeight = 0f;

		logScrollerSkin = (GUISkin)GameObject.Instantiate(skin);
		logScrollerSkin.verticalScrollbar.fixedWidth = size.x * 2f;
		logScrollerSkin.horizontalScrollbar.fixedHeight = 0f;
		logScrollerSkin.verticalScrollbarThumb.fixedWidth = size.x * 2f;
		logScrollerSkin.horizontalScrollbarThumb.fixedHeight = 0f;

		graphScrollerSkin = (GUISkin)GameObject.Instantiate(skin);
		graphScrollerSkin.verticalScrollbar.fixedWidth = 0f;
		graphScrollerSkin.horizontalScrollbar.fixedHeight = size.x * 2f;
		graphScrollerSkin.verticalScrollbarThumb.fixedWidth = 0f;
		graphScrollerSkin.horizontalScrollbarThumb.fixedHeight = size.x * 2f;
		//inGameLogsScrollerSkin.verticalScrollbarThumb.fixedWidth = size.x * 2;
		//inGameLogsScrollerSkin.verticalScrollbar.fixedWidth = size.x * 2;
	}

	void Start()
	{
		logDate = System.DateTime.Now.ToString();
		StartCoroutine("readInfo");
	}

	//clear all logs
	void clear()
	{
		logs.Clear();
		collapsedLogs.Clear();
		currentLog.Clear();
		logsDic.Clear();
		//selectedIndex = -1;
		selectedLog = null;
		numOfLogs = 0;
		numOfLogsWarning = 0;
		numOfLogsError = 0;
		numOfCollapsedLogs = 0;
		numOfCollapsedLogsWarning = 0;
		numOfCollapsedLogsError = 0;
		logsMemUsage = 0;
		graphMemUsage = 0;
		samples.Clear();
		System.GC.Collect();
		selectedLog = null;
	}

	Rect screenRect = Rect.zero;
	Rect toolBarRect = Rect.zero;
	Rect logsRect = Rect.zero;
	Rect stackRect = Rect.zero;
	Rect graphRect = Rect.zero;
	Rect graphMinRect = Rect.zero;
	Rect graphMaxRect = Rect.zero;
	Rect buttomRect = Rect.zero ;
	Vector2 stackRectTopLeft;
	Rect detailRect = Rect.zero;

	Vector2 scrollPosition;
	Vector2 scrollPosition2;
	Vector2 toolbarScrollPosition;

	//int 	selectedIndex = -1;
	Log selectedLog;

	float toolbarOldDrag = 0;
	float oldDrag;
	float oldDrag2;
	float oldDrag3;
	int startIndex;

	//calculate what is the currentLog : collapsed or not , hide or view warnings ......
	void calculateCurrentLog()
	{
		bool filter = !string.IsNullOrEmpty(filterText);
		string _filterText = "";
		if (filter)
			_filterText = filterText.ToLower();
		currentLog.Clear();
		if (collapse) {
			for (int i = 0; i < collapsedLogs.Count; i++) {
				Log log = collapsedLogs[i];
				if (log.logType == _LogType.Log && !showLog)
					continue;
				if (log.logType == _LogType.Warning && !showWarning)
					continue;
				if (log.logType == _LogType.Error && !showError)
					continue;
				if (log.logType == _LogType.Assert && !showError)
					continue;
				if (log.logType == _LogType.Exception && !showError)
					continue;

				if (filter) {
					if (log.condition.ToLower().Contains(_filterText))
						currentLog.Add(log);
				}
				else {
					currentLog.Add(log);
				}
			}
		}
		else {
			for (int i = 0; i < logs.Count; i++) {
				Log log = logs[i];
				if (log.logType == _LogType.Log && !showLog)
					continue;
				if (log.logType == _LogType.Warning && !showWarning)
					continue;
				if (log.logType == _LogType.Error && !showError)
					continue;
				if (log.logType == _LogType.Assert && !showError)
					continue;
				if (log.logType == _LogType.Exception && !showError)
					continue;

				if (filter) {
					if (log.condition.ToLower().Contains(_filterText))
						currentLog.Add(log);
				}
				else {
					currentLog.Add(log);
				}
			}
		}

		if (selectedLog != null) {
			int newSelectedIndex = currentLog.IndexOf(selectedLog);
			if (newSelectedIndex == -1) {
				Log collapsedSelected = logsDic[selectedLog.condition][selectedLog.stacktrace];
				newSelectedIndex = currentLog.IndexOf(collapsedSelected);
				if (newSelectedIndex != -1)
					scrollPosition.y = newSelectedIndex * size.y;
			}
			else {
				scrollPosition.y = newSelectedIndex * size.y;
			}
		}
	}

	Rect countRect = Rect.zero;
	Rect timeRect = Rect.zero;
	Rect timeLabelRect = Rect.zero;
	Rect sceneRect = Rect.zero;
	Rect sceneLabelRect = Rect.zero;
	Rect memoryRect = Rect.zero;
	Rect memoryLabelRect = Rect.zero;
	Rect fpsRect = Rect.zero;
	Rect fpsLabelRect = Rect.zero;
	GUIContent tempContent = new GUIContent();


	Vector2 infoScrollPosition;
	Vector2 oldInfoDrag;
	void DrawInfo()
	{

		GUILayout.BeginArea(screenRect, backStyle);

		Vector2 drag = getDrag();
		if ((drag.x != 0) && (downPos != Vector2.zero)) {
			infoScrollPosition.x -= (drag.x - oldInfoDrag.x);
		}
		if ((drag.y != 0) && (downPos != Vector2.zero)) {
			infoScrollPosition.y += (drag.y - oldInfoDrag.y);
		}
		oldInfoDrag = drag;

		GUI.skin = toolbarScrollerSkin;
		infoScrollPosition = GUILayout.BeginScrollView(infoScrollPosition);
		GUILayout.Space(size.x);
		GUILayout.BeginHorizontal();
		GUILayout.Space(size.x);
		GUILayout.Box(buildFromContent, nonStyle, GUILayout.Width(size.x), GUILayout.Height(size.y));
		GUILayout.Space(size.x);
		GUILayout.Label(buildDate, nonStyle, GUILayout.Height(size.y));
		GUILayout.FlexibleSpace();
		GUILayout.EndHorizontal();

		GUILayout.BeginHorizontal();
		GUILayout.Space(size.x);
		GUILayout.Box(systemInfoContent, nonStyle, GUILayout.Width(size.x), GUILayout.Height(size.y));
		GUILayout.Space(size.x);
		GUILayout.Label(deviceModel, nonStyle, GUILayout.Height(size.y));
		GUILayout.Space(size.x);
		GUILayout.Label(deviceType, nonStyle, GUILayout.Height(size.y));
		GUILayout.Space(size.x);
		GUILayout.Label(deviceName, nonStyle, GUILayout.Height(size.y));
		GUILayout.FlexibleSpace();
		GUILayout.EndHorizontal();

		GUILayout.BeginHorizontal();
		GUILayout.Space(size.x);
		GUILayout.Box(graphicsInfoContent, nonStyle, GUILayout.Width(size.x), GUILayout.Height(size.y));
		GUILayout.Space(size.x);
		GUILayout.Label(SystemInfo.graphicsDeviceName, nonStyle, GUILayout.Height(size.y));
		GUILayout.Space(size.x);
		GUILayout.Label(graphicsMemorySize, nonStyle, GUILayout.Height(size.y));
#if !UNITY_CHANGE1
		GUILayout.Space(size.x);
		GUILayout.Label(maxTextureSize, nonStyle, GUILayout.Height(size.y));
#endif
		GUILayout.FlexibleSpace();
		GUILayout.EndHorizontal();

		GUILayout.BeginHorizontal();
		GUILayout.Space(size.x);
		GUILayout.Space(size.x);
		GUILayout.Space(size.x);
		GUILayout.Label("Screen Width " + Screen.width, nonStyle, GUILayout.Height(size.y));
		GUILayout.Space(size.x);
		GUILayout.Label("Screen Height " + Screen.height, nonStyle, GUILayout.Height(size.y));
		GUILayout.FlexibleSpace();
		GUILayout.EndHorizontal();

		GUILayout.BeginHorizontal();
		GUILayout.Space(size.x);
		GUILayout.Box(showMemoryContent, nonStyle, GUILayout.Width(size.x), GUILayout.Height(size.y));
		GUILayout.Space(size.x);
		GUILayout.Label(systemMemorySize + " mb", nonStyle, GUILayout.Height(size.y));
		GUILayout.FlexibleSpace();
		GUILayout.EndHorizontal();

		GUILayout.BeginHorizontal();
		GUILayout.Space(size.x);
		GUILayout.Space(size.x);
		GUILayout.Space(size.x);
		GUILayout.Label("Mem Usage Of Logs " + logsMemUsage.ToString("0.000") + " mb", nonStyle, GUILayout.Height(size.y));
		GUILayout.Space(size.x);
		//GUILayout.Label( "Mem Usage Of Graph " + graphMemUsage.ToString("0.000")  + " mb", nonStyle , GUILayout.Height(size.y));
		//GUILayout.Space( size.x);
		GUILayout.Label("GC Memory " + gcTotalMemory.ToString("0.000") + " mb", nonStyle, GUILayout.Height(size.y));
		GUILayout.FlexibleSpace();
		GUILayout.EndHorizontal();

		GUILayout.BeginHorizontal();
		GUILayout.Space(size.x);
		GUILayout.Box(softwareContent, nonStyle, GUILayout.Width(size.x), GUILayout.Height(size.y));
		GUILayout.Space(size.x);
		GUILayout.Label(SystemInfo.operatingSystem, nonStyle, GUILayout.Height(size.y));
		GUILayout.FlexibleSpace();
		GUILayout.EndHorizontal();


		GUILayout.BeginHorizontal();
		GUILayout.Space(size.x);
		GUILayout.Box(dateContent, nonStyle, GUILayout.Width(size.x), GUILayout.Height(size.y));
		GUILayout.Space(size.x);
		GUILayout.Label(System.DateTime.Now.ToString(), nonStyle, GUILayout.Height(size.y));
		GUILayout.Label(" - Application Started At " + logDate, nonStyle, GUILayout.Height(size.y));
		GUILayout.FlexibleSpace();
		GUILayout.EndHorizontal();

		GUILayout.BeginHorizontal();
		GUILayout.Space(size.x);
		GUILayout.Box(showTimeContent, nonStyle, GUILayout.Width(size.x), GUILayout.Height(size.y));
		GUILayout.Space(size.x);
		GUILayout.Label(Time.realtimeSinceStartup.ToString("000"), nonStyle, GUILayout.Height(size.y));
		GUILayout.FlexibleSpace();
		GUILayout.EndHorizontal();

		GUILayout.BeginHorizontal();
		GUILayout.Space(size.x);
		GUILayout.Box(showFpsContent, nonStyle, GUILayout.Width(size.x), GUILayout.Height(size.y));
		GUILayout.Space(size.x);
		GUILayout.Label(fpsText, nonStyle, GUILayout.Height(size.y));
		GUILayout.FlexibleSpace();
		GUILayout.EndHorizontal();

		GUILayout.BeginHorizontal();
		GUILayout.Space(size.x);
		GUILayout.Box(userContent, nonStyle, GUILayout.Width(size.x), GUILayout.Height(size.y));
		GUILayout.Space(size.x);
		GUILayout.Label(UserData, nonStyle, GUILayout.Height(size.y));
		GUILayout.FlexibleSpace();
		GUILayout.EndHorizontal();

		GUILayout.BeginHorizontal();
		GUILayout.Space(size.x);
		GUILayout.Box(showSceneContent, nonStyle, GUILayout.Width(size.x), GUILayout.Height(size.y));
		GUILayout.Space(size.x);
		GUILayout.Label(currentScene, nonStyle, GUILayout.Height(size.y));
		GUILayout.FlexibleSpace();
		GUILayout.EndHorizontal();

		GUILayout.BeginHorizontal();
		GUILayout.Space(size.x);
		GUILayout.Box(showSceneContent, nonStyle, GUILayout.Width(size.x), GUILayout.Height(size.y));
		GUILayout.Space(size.x);
		GUILayout.Label("Unity Version = " + Application.unityVersion, nonStyle, GUILayout.Height(size.y));
		GUILayout.FlexibleSpace();
		GUILayout.EndHorizontal();

		/*GUILayout.BeginHorizontal();
		GUILayout.Space( size.x);
		GUILayout.Box( graphContent ,nonStyle ,  GUILayout.Width(size.x) , GUILayout.Height(size.y));
		GUILayout.Space( size.x);
		GUILayout.Label( "frame " + samples.Count , nonStyle , GUILayout.Height(size.y));
		GUILayout.FlexibleSpace();
		GUILayout.EndHorizontal();*/

		drawInfo_enableDisableToolBarButtons();

		GUILayout.FlexibleSpace();

		GUILayout.BeginHorizontal();
		GUILayout.Space(size.x);
		GUILayout.Label("Size = " + size.x.ToString("0.0"), nonStyle, GUILayout.Height(size.y));
		GUILayout.Space(size.x);
		float _size = GUILayout.HorizontalSlider(size.x, 16, 64, sliderBackStyle, sliderThumbStyle, GUILayout.Width(Screen.width * 0.5f));
		if (size.x != _size) {
			size.x = size.y = _size;
			initializeStyle();
		}
		GUILayout.FlexibleSpace();
		GUILayout.EndHorizontal();

		GUILayout.BeginHorizontal();
		GUILayout.Space(size.x);
		if (GUILayout.Button(backContent, barStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2))) {
			currentView = ReportView.Logs;
		}
		GUILayout.FlexibleSpace();
		GUILayout.EndHorizontal();



		GUILayout.EndScrollView();

		GUILayout.EndArea();
	}


	void drawInfo_enableDisableToolBarButtons()
	{
		GUILayout.BeginHorizontal();
		GUILayout.Space(size.x);
		GUILayout.Label("Hide or Show tool bar buttons", nonStyle, GUILayout.Height(size.y));
		GUILayout.Space(size.x);
		GUILayout.FlexibleSpace();
		GUILayout.EndHorizontal();

		GUILayout.BeginHorizontal();
		GUILayout.Space(size.x);

		if (GUILayout.Button(clearOnNewSceneContent, (showClearOnNewSceneLoadedButton) ? buttonActiveStyle : barStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2))) {
			showClearOnNewSceneLoadedButton = !showClearOnNewSceneLoadedButton;
		}

		if (GUILayout.Button(showTimeContent, (showTimeButton) ? buttonActiveStyle : barStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2))) {
			showTimeButton = !showTimeButton;
		}
		tempRect = GUILayoutUtility.GetLastRect();
		GUI.Label(tempRect, Time.realtimeSinceStartup.ToString("0.0"), lowerLeftFontStyle);
		if (GUILayout.Button(showSceneContent, (showSceneButton) ? buttonActiveStyle : barStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2))) {
			showSceneButton = !showSceneButton;
		}
		tempRect = GUILayoutUtility.GetLastRect();
		GUI.Label(tempRect, currentScene, lowerLeftFontStyle);
		if (GUILayout.Button(showMemoryContent, (showMemButton) ? buttonActiveStyle : barStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2))) {
			showMemButton = !showMemButton;
		}
		tempRect = GUILayoutUtility.GetLastRect();
		GUI.Label(tempRect, gcTotalMemory.ToString("0.0"), lowerLeftFontStyle);

		if (GUILayout.Button(showFpsContent, (showFpsButton) ? buttonActiveStyle : barStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2))) {
			showFpsButton = !showFpsButton;
		}
		tempRect = GUILayoutUtility.GetLastRect();
		GUI.Label(tempRect, fpsText, lowerLeftFontStyle);
		/*if( GUILayout.Button( graphContent , (showGraph)?buttonActiveStyle:barStyle , GUILayout.Width(size.x*2) ,GUILayout.Height(size.y*2)))
		{
			showGraph = !showGraph ;
		}
		tempRect = GUILayoutUtility.GetLastRect();
		GUI.Label( tempRect , samples.Count.ToString() , lowerLeftFontStyle );*/
		if (GUILayout.Button(searchContent, (showSearchText) ? buttonActiveStyle : barStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2))) {
			showSearchText = !showSearchText;
		}
        if (GUILayout.Button(copyContent, (showCopyButton) ? buttonActiveStyle : barStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2)))
        {
            showCopyButton = !showCopyButton;
        }
        if (GUILayout.Button(copyAllContent, (showCopyAllButton) ? buttonActiveStyle : barStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2)))
        {
            showCopyAllButton = !showCopyAllButton;
        }
        if (GUILayout.Button(saveLogsContent, (showSaveButton) ? buttonActiveStyle : barStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2)))
        {
            showSaveButton = !showSaveButton;
        }
        tempRect = GUILayoutUtility.GetLastRect();
		GUI.TextField(tempRect, filterText, searchStyle);


		GUILayout.FlexibleSpace();
		GUILayout.EndHorizontal();
	}

	void DrawReport()
	{
		screenRect.x = 0f;
		screenRect.y = 0f;
		screenRect.width = Screen.width;
		screenRect.height = Screen.height;
		GUILayout.BeginArea(screenRect, backStyle);
		GUILayout.BeginVertical();
		GUILayout.FlexibleSpace();

		GUILayout.BeginHorizontal();
		GUILayout.FlexibleSpace();
		/*GUILayout.Box( cameraContent ,nonStyle ,  GUILayout.Width(size.x) , GUILayout.Height(size.y));
		GUILayout.FlexibleSpace();*/
		GUILayout.Label("Select Photo", nonStyle, GUILayout.Height(size.y));
		GUILayout.FlexibleSpace();
		GUILayout.EndHorizontal();

		GUILayout.BeginHorizontal();
		GUILayout.Label("Coming Soon", nonStyle, GUILayout.Height(size.y));
		GUILayout.EndHorizontal();

		GUILayout.BeginHorizontal();
		GUILayout.FlexibleSpace();
		if (GUILayout.Button(backContent, barStyle, GUILayout.Width(size.x), GUILayout.Height(size.y))) {
			currentView = ReportView.Logs;
		}
		GUILayout.FlexibleSpace();
		GUILayout.EndHorizontal();

		GUILayout.FlexibleSpace();
		GUILayout.EndVertical();
		GUILayout.EndArea();
	}

	void drawToolBar()
	{

		toolBarRect.x = 0f;
		toolBarRect.y = 0f;
		toolBarRect.width = Screen.width;
		toolBarRect.height = size.y * 2f;

		//toolbarScrollerSkin.verticalScrollbar.fixedWidth = 0f;
		//toolbarScrollerSkin.horizontalScrollbar.fixedHeight= 0f  ;

		GUI.skin = toolbarScrollerSkin;
		Vector2 drag = getDrag();
		if ((drag.x != 0) && (downPos != Vector2.zero) && (downPos.y > Screen.height - size.y * 2f)) {
			toolbarScrollPosition.x -= (drag.x - toolbarOldDrag);
		}
		toolbarOldDrag = drag.x;
		GUILayout.BeginArea(toolBarRect);
		toolbarScrollPosition = GUILayout.BeginScrollView(toolbarScrollPosition);
		GUILayout.BeginHorizontal(barStyle);

		if (GUILayout.Button(clearContent, barStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2))) {
			clear();
		}
		if (GUILayout.Button(collapseContent, (collapse) ? buttonActiveStyle : barStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2))) {
			collapse = !collapse;
			calculateCurrentLog();
		}
		if (showClearOnNewSceneLoadedButton && GUILayout.Button(clearOnNewSceneContent, (clearOnNewSceneLoaded) ? buttonActiveStyle : barStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2))) {
			clearOnNewSceneLoaded = !clearOnNewSceneLoaded;
		}

		if (showTimeButton && GUILayout.Button(showTimeContent, (showTime) ? buttonActiveStyle : barStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2))) {
			showTime = !showTime;
		}
		if (showSceneButton) {
			tempRect = GUILayoutUtility.GetLastRect();
			GUI.Label(tempRect, Time.realtimeSinceStartup.ToString("0.0"), lowerLeftFontStyle);
			if (GUILayout.Button(showSceneContent, (showScene) ? buttonActiveStyle : barStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2))) {
				showScene = !showScene;
			}
			tempRect = GUILayoutUtility.GetLastRect();
			GUI.Label(tempRect, currentScene, lowerLeftFontStyle);
		}
		if (showMemButton) {
			if (GUILayout.Button(showMemoryContent, (showMemory) ? buttonActiveStyle : barStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2))) {
				showMemory = !showMemory;
			}
			tempRect = GUILayoutUtility.GetLastRect();
			GUI.Label(tempRect, gcTotalMemory.ToString("0.0"), lowerLeftFontStyle);
		}
		if (showFpsButton) {
			if (GUILayout.Button(showFpsContent, (showFps) ? buttonActiveStyle : barStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2))) {
				showFps = !showFps;
			}
			tempRect = GUILayoutUtility.GetLastRect();
			GUI.Label(tempRect, fpsText, lowerLeftFontStyle);
		}
		/*if( GUILayout.Button( graphContent , (showGraph)?buttonActiveStyle:barStyle , GUILayout.Width(size.x*2) ,GUILayout.Height(size.y*2)))
		{
			showGraph = !showGraph ;
		}
		tempRect = GUILayoutUtility.GetLastRect();
		GUI.Label( tempRect , samples.Count.ToString() , lowerLeftFontStyle );*/

		if (showSearchText) {
			GUILayout.Box(searchContent, barStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2));
			tempRect = GUILayoutUtility.GetLastRect();
			string newFilterText = GUI.TextField(tempRect, filterText, searchStyle);
			if (newFilterText != filterText) {
				filterText = newFilterText;
				calculateCurrentLog();
			}
		}

        if (showCopyButton)
        {
            if (GUILayout.Button(copyContent, barStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2)))
            {
                if (selectedLog == null)
                    GUIUtility.systemCopyBuffer = "No log selected";
                else
                    GUIUtility.systemCopyBuffer = selectedLog.condition + System.Environment.NewLine + System.Environment.NewLine  + selectedLog.stacktrace;
            }
        }

        if (showCopyAllButton)
        {
            if (GUILayout.Button(copyAllContent, barStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2)))
            {
                string allLogsToClipboard = string.Empty;
                logs.ForEach(l => allLogsToClipboard += l.condition + System.Environment.NewLine + System.Environment.NewLine + l.stacktrace);

                if(string.IsNullOrWhiteSpace(allLogsToClipboard))
                    GUIUtility.systemCopyBuffer = "No log selected";
                else
                    GUIUtility.systemCopyBuffer = allLogsToClipboard;
            }
        }

        if (showSaveButton)
        {
            if (GUILayout.Button(saveLogsContent, barStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2)))
            {
                SaveLogsToDevice();
            }
        }

        if (GUILayout.Button(infoContent, barStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2))) {
			currentView = ReportView.Info;
		}
       


        GUILayout.FlexibleSpace();


		string logsText = " ";
		if (collapse) {
			logsText += numOfCollapsedLogs;
		}
		else {
			logsText += numOfLogs;
		}
		string logsWarningText = " ";
		if (collapse) {
			logsWarningText += numOfCollapsedLogsWarning;
		}
		else {
			logsWarningText += numOfLogsWarning;
		}
		string logsErrorText = " ";
		if (collapse) {
			logsErrorText += numOfCollapsedLogsError;
		}
		else {
			logsErrorText += numOfLogsError;
		}

		GUILayout.BeginHorizontal((showLog) ? buttonActiveStyle : barStyle);
		if (GUILayout.Button(logContent, nonStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2))) {
			showLog = !showLog;
			calculateCurrentLog();
		}
		if (GUILayout.Button(logsText, nonStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2))) {
			showLog = !showLog;
			calculateCurrentLog();
		}
		GUILayout.EndHorizontal();
		GUILayout.BeginHorizontal((showWarning) ? buttonActiveStyle : barStyle);
		if (GUILayout.Button(warningContent, nonStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2))) {
			showWarning = !showWarning;
			calculateCurrentLog();
		}
		if (GUILayout.Button(logsWarningText, nonStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2))) {
			showWarning = !showWarning;
			calculateCurrentLog();
		}
		GUILayout.EndHorizontal();
		GUILayout.BeginHorizontal((showError) ? buttonActiveStyle : nonStyle);
		if (GUILayout.Button(errorContent, nonStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2))) {
			showError = !showError;
			calculateCurrentLog();
		}
		if (GUILayout.Button(logsErrorText, nonStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2))) {
			showError = !showError;
			calculateCurrentLog();
		}
		GUILayout.EndHorizontal();

		if (GUILayout.Button(closeContent, barStyle, GUILayout.Width(size.x * 2), GUILayout.Height(size.y * 2))) {
			show = false;
			ReporterGUI gui = gameObject.GetComponent<ReporterGUI>();
			DestroyImmediate(gui);

			try {
				gameObject.SendMessage("OnHideReporter");
			}
			catch (System.Exception e) {
				Debug.LogException(e);
			}
		}


		GUILayout.EndHorizontal();

		GUILayout.EndScrollView();

		GUILayout.EndArea();
	}


	Rect tempRect;
	void DrawLogs()
	{

		GUILayout.BeginArea(logsRect, backStyle);

		GUI.skin = logScrollerSkin;
		//setStartPos();
		Vector2 drag = getDrag();

		if (drag.y != 0 && logsRect.Contains(new Vector2(downPos.x, Screen.height - downPos.y))) {
			scrollPosition.y += (drag.y - oldDrag);
		}
		scrollPosition = GUILayout.BeginScrollView(scrollPosition);

		oldDrag = drag.y;


		int totalVisibleCount = (int)(Screen.height * 0.75f / size.y);
		int totalCount = currentLog.Count;
		/*if( totalCount < 100 )
			inGameLogsScrollerSkin.verticalScrollbarThumb.fixedHeight = 0;
		else 
			inGameLogsScrollerSkin.verticalScrollbarThumb.fixedHeight = 64;*/

		totalVisibleCount = Mathf.Min(totalVisibleCount, totalCount - startIndex);
		int index = 0;
		int beforeHeight = (int)(startIndex * size.y);
		//selectedIndex = Mathf.Clamp( selectedIndex , -1 , totalCount -1);
		if (beforeHeight > 0) {
			//fill invisible gap before scroller to make proper scroller pos
			GUILayout.BeginHorizontal(GUILayout.Height(beforeHeight));
			GUILayout.Label("---");
			GUILayout.EndHorizontal();
		}

		int endIndex = startIndex + totalVisibleCount;
		endIndex = Mathf.Clamp(endIndex, 0, totalCount);
		bool scrollerVisible = (totalVisibleCount < totalCount);
		for (int i = startIndex; (startIndex + index) < endIndex; i++) {

			if (i >= currentLog.Count)
				break;
			Log log = currentLog[i];

			if (log.logType == _LogType.Log && !showLog)
				continue;
			if (log.logType == _LogType.Warning && !showWarning)
				continue;
			if (log.logType == _LogType.Error && !showError)
				continue;
			if (log.logType == _LogType.Assert && !showError)
				continue;
			if (log.logType == _LogType.Exception && !showError)
				continue;

			if (index >= totalVisibleCount) {
				break;
			}

			GUIContent content = null;
			if (log.logType == _LogType.Log)
				content = logContent;
			else if (log.logType == _LogType.Warning)
				content = warningContent;
			else
				content = errorContent;
			//content.text = log.condition ;

			GUIStyle currentLogStyle = ((startIndex + index) % 2 == 0) ? evenLogStyle : oddLogStyle;
			if (log == selectedLog) {
				//selectedLog = log ;
				currentLogStyle = selectedLogStyle;
			}
			else {
			}

			tempContent.text = log.count.ToString();
			float w = 0f;
			if (collapse)
				w = barStyle.CalcSize(tempContent).x + 3;
			countRect.x = Screen.width - w;
			countRect.y = size.y * i;
			if (beforeHeight > 0)
				countRect.y += 8;//i will check later why
			countRect.width = w;
			countRect.height = size.y;

			if (scrollerVisible)
				countRect.x -= size.x * 2;

			Sample sample = samples[log.sampleId];
			fpsRect = countRect;
			if (showFps) {
				tempContent.text = sample.fpsText;
				w = currentLogStyle.CalcSize(tempContent).x + size.x;
				fpsRect.x -= w;
				fpsRect.width = size.x;
				fpsLabelRect = fpsRect;
				fpsLabelRect.x += size.x;
				fpsLabelRect.width = w - size.x;
			}


			memoryRect = fpsRect;
			if (showMemory) {
				tempContent.text = sample.memory.ToString("0.000");
				w = currentLogStyle.CalcSize(tempContent).x + size.x;
				memoryRect.x -= w;
				memoryRect.width = size.x;
				memoryLabelRect = memoryRect;
				memoryLabelRect.x += size.x;
				memoryLabelRect.width = w - size.x;
			}
			sceneRect = memoryRect;
			if (showScene) {

				tempContent.text = sample.GetSceneName();
				w = currentLogStyle.CalcSize(tempContent).x + size.x;
				sceneRect.x -= w;
				sceneRect.width = size.x;
				sceneLabelRect = sceneRect;
				sceneLabelRect.x += size.x;
				sceneLabelRect.width = w - size.x;
			}
			timeRect = sceneRect;
			if (showTime) {
				tempContent.text = sample.time.ToString("0.000");
				w = currentLogStyle.CalcSize(tempContent).x + size.x;
				timeRect.x -= w;
				timeRect.width = size.x;
				timeLabelRect = timeRect;
				timeLabelRect.x += size.x;
				timeLabelRect.width = w - size.x;
			}



			GUILayout.BeginHorizontal(currentLogStyle);
			if (log == selectedLog) {
				GUILayout.Box(content, nonStyle, GUILayout.Width(size.x), GUILayout.Height(size.y));
				GUILayout.Label(log.condition, selectedLogFontStyle);
				//GUILayout.FlexibleSpace();
				if (showTime) {
					GUI.Box(timeRect, showTimeContent, currentLogStyle);
					GUI.Label(timeLabelRect, sample.time.ToString("0.000"), currentLogStyle);
				}
				if (showScene) {
					GUI.Box(sceneRect, showSceneContent, currentLogStyle);
					GUI.Label(sceneLabelRect, sample.GetSceneName(), currentLogStyle);
				}
				if (showMemory) {
					GUI.Box(memoryRect, showMemoryContent, currentLogStyle);
					GUI.Label(memoryLabelRect, sample.memory.ToString("0.000") + " mb", currentLogStyle);
				}
				if (showFps) {
					GUI.Box(fpsRect, showFpsContent, currentLogStyle);
					GUI.Label(fpsLabelRect, sample.fpsText, currentLogStyle);
				}


			}
			else {
				if (GUILayout.Button(content, nonStyle, GUILayout.Width(size.x), GUILayout.Height(size.y))) {
					//selectedIndex = startIndex + index ;
					selectedLog = log;
				}
				if (GUILayout.Button(log.condition, logButtonStyle)) {
					//selectedIndex = startIndex + index ;
					selectedLog = log;
				}
				//GUILayout.FlexibleSpace();
				if (showTime) {
					GUI.Box(timeRect, showTimeContent, currentLogStyle);
					GUI.Label(timeLabelRect, sample.time.ToString("0.000"), currentLogStyle);
				}
				if (showScene) {
					GUI.Box(sceneRect, showSceneContent, currentLogStyle);
					GUI.Label(sceneLabelRect, sample.GetSceneName(), currentLogStyle);
				}
				if (showMemory) {
					GUI.Box(memoryRect, showMemoryContent, currentLogStyle);
					GUI.Label(memoryLabelRect, sample.memory.ToString("0.000") + " mb", currentLogStyle);
				}
				if (showFps) {
					GUI.Box(fpsRect, showFpsContent, currentLogStyle);
					GUI.Label(fpsLabelRect, sample.fpsText, currentLogStyle);
				}
			}
			if (collapse)
				GUI.Label(countRect, log.count.ToString(), barStyle);
			GUILayout.EndHorizontal();
			index++;
		}

		int afterHeight = (int)((totalCount - (startIndex + totalVisibleCount)) * size.y);
		if (afterHeight > 0) {
			//fill invisible gap after scroller to make proper scroller pos
			GUILayout.BeginHorizontal(GUILayout.Height(afterHeight));
			GUILayout.Label(" ");
			GUILayout.EndHorizontal();
		}

		GUILayout.EndScrollView();
		GUILayout.EndArea();

		buttomRect.x = 0f;
		buttomRect.y = Screen.height - size.y;
		buttomRect.width = Screen.width;
		buttomRect.height = size.y;

		if (showGraph)
			drawGraph();
		else
			drawStack();
	}


	float graphSize = 4f;
	int startFrame = 0;
	int currentFrame = 0;
	Vector3 tempVector1;
	Vector3 tempVector2;
	Vector2 graphScrollerPos;
	float maxFpsValue;
	float minFpsValue;
	float maxMemoryValue;
	float minMemoryValue;

	void drawGraph()
	{

		graphRect = stackRect;
		graphRect.height = Screen.height * 0.25f;//- size.y ;



		//startFrame = samples.Count - (int)(Screen.width / graphSize) ;
		//if( startFrame < 0 ) startFrame = 0 ;
		GUI.skin = graphScrollerSkin;

		Vector2 drag = getDrag();
		if (graphRect.Contains(new Vector2(downPos.x, Screen.height - downPos.y))) {
			if (drag.x != 0) {
				graphScrollerPos.x -= drag.x - oldDrag3;
				graphScrollerPos.x = Mathf.Max(0, graphScrollerPos.x);
			}

			Vector2 p = downPos;
			if (p != Vector2.zero) {
				currentFrame = startFrame + (int)(p.x / graphSize);
			}
		}

		oldDrag3 = drag.x;
		GUILayout.BeginArea(graphRect, backStyle);

		graphScrollerPos = GUILayout.BeginScrollView(graphScrollerPos);
		startFrame = (int)(graphScrollerPos.x / graphSize);
		if (graphScrollerPos.x >= (samples.Count * graphSize - Screen.width))
			graphScrollerPos.x += graphSize;

		GUILayout.Label(" ", GUILayout.Width(samples.Count * graphSize));
		GUILayout.EndScrollView();
		GUILayout.EndArea();
		maxFpsValue = 0;
		minFpsValue = 100000;
		maxMemoryValue = 0;
		minMemoryValue = 100000;
		for (int i = 0; i < Screen.width / graphSize; i++) {
			int index = startFrame + i;
			if (index >= samples.Count)
				break;
			Sample s = samples[index];
			if (maxFpsValue < s.fps) maxFpsValue = s.fps;
			if (minFpsValue > s.fps) minFpsValue = s.fps;
			if (maxMemoryValue < s.memory) maxMemoryValue = s.memory;
			if (minMemoryValue > s.memory) minMemoryValue = s.memory;
		}

		//GUI.BeginGroup(graphRect);


		if (currentFrame != -1 && currentFrame < samples.Count) {
			Sample selectedSample = samples[currentFrame];
			GUILayout.BeginArea(buttomRect, backStyle);
			GUILayout.BeginHorizontal();

			GUILayout.Box(showTimeContent, nonStyle, GUILayout.Width(size.x), GUILayout.Height(size.y));
			GUILayout.Label(selectedSample.time.ToString("0.0"), nonStyle);
			GUILayout.Space(size.x);

			GUILayout.Box(showSceneContent, nonStyle, GUILayout.Width(size.x), GUILayout.Height(size.y));
			GUILayout.Label(selectedSample.GetSceneName(), nonStyle);
			GUILayout.Space(size.x);

			GUILayout.Box(showMemoryContent, nonStyle, GUILayout.Width(size.x), GUILayout.Height(size.y));
			GUILayout.Label(selectedSample.memory.ToString("0.000"), nonStyle);
			GUILayout.Space(size.x);

			GUILayout.Box(showFpsContent, nonStyle, GUILayout.Width(size.x), GUILayout.Height(size.y));
			GUILayout.Label(selectedSample.fpsText, nonStyle);
			GUILayout.Space(size.x);

			/*GUILayout.Box( graphContent ,nonStyle, GUILayout.Width(size.x) ,GUILayout.Height(size.y));
			GUILayout.Label( currentFrame.ToString() ,nonStyle  );*/
			GUILayout.FlexibleSpace();
			GUILayout.EndHorizontal();
			GUILayout.EndArea();
		}

		graphMaxRect = stackRect;
		graphMaxRect.height = size.y;
		GUILayout.BeginArea(graphMaxRect);
		GUILayout.BeginHorizontal();

		GUILayout.Box(showMemoryContent, nonStyle, GUILayout.Width(size.x), GUILayout.Height(size.y));
		GUILayout.Label(maxMemoryValue.ToString("0.000"), nonStyle);

		GUILayout.Box(showFpsContent, nonStyle, GUILayout.Width(size.x), GUILayout.Height(size.y));
		GUILayout.Label(maxFpsValue.ToString("0.000"), nonStyle);
		GUILayout.FlexibleSpace();
		GUILayout.EndHorizontal();
		GUILayout.EndArea();

		graphMinRect = stackRect;
		graphMinRect.y = stackRect.y + stackRect.height - size.y;
		graphMinRect.height = size.y;
		GUILayout.BeginArea(graphMinRect);
		GUILayout.BeginHorizontal();

		GUILayout.Box(showMemoryContent, nonStyle, GUILayout.Width(size.x), GUILayout.Height(size.y));

		GUILayout.Label(minMemoryValue.ToString("0.000"), nonStyle);


		GUILayout.Box(showFpsContent, nonStyle, GUILayout.Width(size.x), GUILayout.Height(size.y));

		GUILayout.Label(minFpsValue.ToString("0.000"), nonStyle);
		GUILayout.FlexibleSpace();
		GUILayout.EndHorizontal();
		GUILayout.EndArea();

		//GUI.EndGroup();
	}

	void drawStack()
	{

		if (selectedLog != null) {
			Vector2 drag = getDrag();
			if (drag.y != 0 && stackRect.Contains(new Vector2(downPos.x, Screen.height - downPos.y))) {
				scrollPosition2.y += drag.y - oldDrag2;
			}
			oldDrag2 = drag.y;



			GUILayout.BeginArea(stackRect, backStyle);
			scrollPosition2 = GUILayout.BeginScrollView(scrollPosition2);
			Sample selectedSample = null;
			try {
				selectedSample = samples[selectedLog.sampleId];
			}
			catch (System.Exception e) {
				Debug.LogException(e);
			}

			GUILayout.BeginHorizontal();
			GUILayout.Label(selectedLog.condition, stackLabelStyle);
			GUILayout.EndHorizontal();
			GUILayout.Space(size.y * 0.25f);
			GUILayout.BeginHorizontal();
			GUILayout.Label(selectedLog.stacktrace, stackLabelStyle);
			GUILayout.EndHorizontal();
			GUILayout.Space(size.y);
			GUILayout.EndScrollView();
			GUILayout.EndArea();


			GUILayout.BeginArea(buttomRect, backStyle);
			GUILayout.BeginHorizontal();

			GUILayout.Box(showTimeContent, nonStyle, GUILayout.Width(size.x), GUILayout.Height(size.y));
			GUILayout.Label(selectedSample.time.ToString("0.000"), nonStyle);
			GUILayout.Space(size.x);

			GUILayout.Box(showSceneContent, nonStyle, GUILayout.Width(size.x), GUILayout.Height(size.y));
			GUILayout.Label(selectedSample.GetSceneName(), nonStyle);
			GUILayout.Space(size.x);

			GUILayout.Box(showMemoryContent, nonStyle, GUILayout.Width(size.x), GUILayout.Height(size.y));
			GUILayout.Label(selectedSample.memory.ToString("0.000"), nonStyle);
			GUILayout.Space(size.x);

			GUILayout.Box(showFpsContent, nonStyle, GUILayout.Width(size.x), GUILayout.Height(size.y));
			GUILayout.Label(selectedSample.fpsText, nonStyle);
			/*GUILayout.Space( size.x );
			GUILayout.Box( graphContent ,nonStyle, GUILayout.Width(size.x) ,GUILayout.Height(size.y));
			GUILayout.Label( selectedLog.sampleId.ToString() ,nonStyle  );*/
			GUILayout.FlexibleSpace();
			GUILayout.EndHorizontal();
			GUILayout.EndArea();



		}
		else {
			GUILayout.BeginArea(stackRect, backStyle);
			GUILayout.EndArea();
			GUILayout.BeginArea(buttomRect, backStyle);
			GUILayout.EndArea();
		}

	}


	public void OnGUIDraw()
	{

		if (!show) {
			return;
		}

		screenRect.x = 0;
		screenRect.y = 0;
		screenRect.width = Screen.width;
		screenRect.height = Screen.height;

		getDownPos();


		logsRect.x = 0f;
		logsRect.y = size.y * 2f;
		logsRect.width = Screen.width;
		logsRect.height = Screen.height * 0.75f - size.y * 2f;

		stackRectTopLeft.x = 0f;
		stackRect.x = 0f;
		stackRectTopLeft.y = Screen.height * 0.75f;
		stackRect.y = Screen.height * 0.75f;
		stackRect.width = Screen.width;
		stackRect.height = Screen.height * 0.25f - size.y;



		detailRect.x = 0f;
		detailRect.y = Screen.height - size.y * 3;
		detailRect.width = Screen.width;
		detailRect.height = size.y * 3;

		if (currentView == ReportView.Info)
			DrawInfo();
		else if (currentView == ReportView.Logs) {
			drawToolBar();
			DrawLogs();
		}


	}

	List<Vector2> gestureDetector = new List<Vector2>();
	Vector2 gestureSum = Vector2.zero;
	float gestureLength = 0;
	int gestureCount = 0;
	bool isGestureDone()
	{
		// 【MuMu/模拟器适配】原版在 Android 上只认 Input.touches —— 但模拟器里
		// 用电脑鼠标操作时系统注入的是鼠标事件，touches 恒为空，画圈永远无效。
		// 改成"触摸 + 鼠标"双轨：有一根手指走 touch，没有手指但鼠标按下走 mouse。
		bool dragging = false;
		Vector2 p = Vector2.zero;

		if (Application.platform == RuntimePlatform.Android ||
			Application.platform == RuntimePlatform.IPhonePlayer) {
			if (Input.touchCount == 1) {
				Touch t = Input.touches[0];
				if (t.phase == TouchPhase.Canceled || t.phase == TouchPhase.Ended) {
					gestureDetector.Clear();
					gestureCount = 0;
				}
				else if (t.phase == TouchPhase.Moved) {
					dragging = true;
					p = t.position;
				}
			}
			else if (Input.touchCount == 0 && Input.GetMouseButton(0)) {
				// 模拟器鼠标路径
				dragging = true;
				p = Input.mousePosition;
			}
			else {
				gestureDetector.Clear();
				gestureCount = 0;
			}
		}
		else {
			if (Input.GetMouseButtonUp(0)) {
				gestureDetector.Clear();
				gestureCount = 0;
			}
			else {
				if (Input.GetMouseButton(0)) {
					dragging = true;
					p = new Vector2(Input.mousePosition.x, Input.mousePosition.y);
				}
			}
		}

		if (dragging) {
			if (gestureDetector.Count == 0 || (p - gestureDetector[gestureDetector.Count - 1]).magnitude > 10)
				gestureDetector.Add(p);
		}

		if (gestureDetector.Count < 10)
			return false;

		gestureSum = Vector2.zero;
		gestureLength = 0;
		Vector2 prevDelta = Vector2.zero;
		for (int i = 0; i < gestureDetector.Count - 2; i++) {

			Vector2 delta = gestureDetector[i + 1] - gestureDetector[i];
			float deltaLength = delta.magnitude;
			gestureSum += delta;
			gestureLength += deltaLength;

			float dot = Vector2.Dot(delta, prevDelta);
			if (dot < 0f) {
				gestureDetector.Clear();
				gestureCount = 0;
				return false;
			}

			prevDelta = delta;
		}

		int gestureBase = (Screen.width + Screen.height) / 4;

		if (gestureLength > gestureBase && gestureSum.magnitude < gestureBase / 2) {
			gestureDetector.Clear();
			gestureCount++;
			if (gestureCount >= numOfCircleToShow)
				return true;
		}

		return false;
	}

	float lastClickTime = -1;

	// 【双击调出】两次"按下"间隔 < DoubleClickInterval 视为双击。
	// 原版阈值 0.2s 在鼠标/模拟器上偏紧，放宽到 0.35s（仍属标准双击区间）；
	// 画圈在模拟器里较难完成，双击是主要的备用调起方式（见 Update）。
	const float DoubleClickInterval = 0.35f;

	bool RegisterClickForDoubleClick()
	{
		if (lastClickTime == -1) {
			lastClickTime = Time.realtimeSinceStartup;
			return false;
		}
		if (Time.realtimeSinceStartup - lastClickTime < DoubleClickInterval) {
			lastClickTime = -1;
			return true;
		}
		lastClickTime = Time.realtimeSinceStartup;
		return false;
	}

	bool isDoubleClickDone()
	{
		// 【MuMu/模拟器适配】与 isGestureDone 同款双轨：有一根手指走触摸；
		// 没有手指但鼠标按下（模拟器鼠标未映射成触摸的场景）走鼠标。
		if (Application.platform == RuntimePlatform.Android ||
		   Application.platform == RuntimePlatform.IPhonePlayer) {
			if (Input.touchCount == 1) {
				if (Input.touches[0].phase == TouchPhase.Began) {
					return RegisterClickForDoubleClick();
				}
			}
			else if (Input.touchCount == 0) {
				if (Input.GetMouseButtonDown(0)) {
					return RegisterClickForDoubleClick();
				}
			}
			else {
				lastClickTime = -1;   // 多指同时按下不算点击
			}
		}
		else {
			if (Input.GetMouseButtonDown(0)) {
				return RegisterClickForDoubleClick();
			}
		}
		return false;
	}

	//calculate  pos of first click on screen
	Vector2 startPos;

	Vector2 downPos;
	Vector2 getDownPos()
	{
		if (Application.platform == RuntimePlatform.Android ||
		   Application.platform == RuntimePlatform.IPhonePlayer) {

			if (Input.touches.Length == 1 && Input.touches[0].phase == TouchPhase.Began) {
				downPos = Input.touches[0].position;
				return downPos;
			}
		}
		else {
			if (Input.GetMouseButtonDown(0)) {
				downPos.x = Input.mousePosition.x;
				downPos.y = Input.mousePosition.y;
				return downPos;
			}
		}

		return Vector2.zero;
	}
	//calculate drag amount , this is used for scrolling

	Vector2 mousePosition;
	Vector2 getDrag()
	{

		if (Application.platform == RuntimePlatform.Android ||
			Application.platform == RuntimePlatform.IPhonePlayer) {
			if (Input.touches.Length != 1) {
				return Vector2.zero;
			}
			return Input.touches[0].position - downPos;
		}
		else {
			if (Input.GetMouseButton(0)) {
				mousePosition = Input.mousePosition;
				return mousePosition - downPos;
			}
			else {
				return Vector2.zero;
			}
		}
	}

	//calculate the start index of visible log
	void calculateStartIndex()
	{
		startIndex = (int)(scrollPosition.y / size.y);
		startIndex = Mathf.Clamp(startIndex, 0, currentLog.Count);
	}

	// For FPS Counter
	private int frames = 0;
	private bool firstTime = true;
	private float lastUpdate = 0f;
	private const int requiredFrames = 10;
	private const float updateInterval = 0.25f;

#if UNITY_CHANGE1
	float lastUpdate2 = 0;
#endif

	void doShow()
	{
		show = true;
		currentView = ReportView.Logs;
		gameObject.AddComponent<ReporterGUI>();
		Debug.Log("[Reporter] 调试面板已打开");


		try {
			gameObject.SendMessage("OnShowReporter");
		}
		catch (System.Exception e) {
			Debug.LogException(e);
		}
	}

	void Update()
	{
		fpsText = fps.ToString("0.000");
		gcTotalMemory = (((float)System.GC.GetTotalMemory(false)) / 1024 / 1024);
		//addSample();

#if UNITY_CHANGE3
		int sceneIndex = SceneManager.GetActiveScene().buildIndex ;
		if( sceneIndex != -1 && string.IsNullOrEmpty( scenes[sceneIndex] ))
			scenes[ SceneManager.GetActiveScene().buildIndex ] = SceneManager.GetActiveScene().name ;
#else
		int sceneIndex = Application.loadedLevel;
		if (sceneIndex != -1 && string.IsNullOrEmpty(scenes[Application.loadedLevel]))
			scenes[Application.loadedLevel] = Application.loadedLevelName;
#endif

		calculateStartIndex();
		if (!show && (isGestureDone() || isDoubleClickDone())) {
			doShow();
		}


		if (threadedLogs.Count > 0) {
			lock (threadedLogs) {
				for (int i = 0; i < threadedLogs.Count; i++) {
					Log l = threadedLogs[i];
					AddLog(l.condition, l.stacktrace, (LogType)l.logType);
				}
				threadedLogs.Clear();
			}
		}

#if UNITY_CHANGE1
		float elapsed2 = Time.realtimeSinceStartup - lastUpdate2;
		if (elapsed2 > 1) {
			lastUpdate2 = Time.realtimeSinceStartup;
			//be sure no body else take control of log 
			Application.RegisterLogCallback (new Application.LogCallback (CaptureLog));
			Application.RegisterLogCallbackThreaded (new Application.LogCallback (CaptureLogThread));
		}
#endif

		// FPS Counter
		if (firstTime) {
			firstTime = false;
			lastUpdate = Time.realtimeSinceStartup;
			frames = 0;
			return;
		}
		frames++;
		float dt = Time.realtimeSinceStartup - lastUpdate;
		if (dt > updateInterval && frames > requiredFrames) {
			fps = (float)frames / dt;
			lastUpdate = Time.realtimeSinceStartup;
			frames = 0;
		}
	}


	void CaptureLog(string condition, string stacktrace, LogType type)
	{
		AddLog(condition, stacktrace, type);
	}

	void AddLog(string condition, string stacktrace, LogType type)
	{
		float memUsage = 0f;
		string _condition = "";
		if (cachedString.ContainsKey(condition)) {
			_condition = cachedString[condition];
		}
		else {
			_condition = condition;
			cachedString.Add(_condition, _condition);
			memUsage += (string.IsNullOrEmpty(_condition) ? 0 : _condition.Length * sizeof(char));
			memUsage += System.IntPtr.Size;
		}
		string _stacktrace = "";
		if (cachedString.ContainsKey(stacktrace)) {
			_stacktrace = cachedString[stacktrace];
		}
		else {
			_stacktrace = stacktrace;
			cachedString.Add(_stacktrace, _stacktrace);
			memUsage += (string.IsNullOrEmpty(_stacktrace) ? 0 : _stacktrace.Length * sizeof(char));
			memUsage += System.IntPtr.Size;
		}
		bool newLogAdded = false;

		addSample();
		Log log = new Log() { logType = (_LogType)type, condition = _condition, stacktrace = _stacktrace, sampleId = samples.Count - 1 };
		memUsage += log.GetMemoryUsage();
		//memUsage += samples.Count * 13 ;

		logsMemUsage += memUsage / 1024 / 1024;

		if (TotalMemUsage > maxSize) {
			clear();
			Debug.Log("Memory Usage Reach" + maxSize + " mb So It is Cleared");
			return;
		}

		bool isNew = false;
		//string key = _condition;// + "_!_" + _stacktrace ;
		if (logsDic.ContainsKey(_condition, stacktrace)) {
			isNew = false;
			logsDic[_condition][stacktrace].count++;
		}
		else {
			isNew = true;
			collapsedLogs.Add(log);
			logsDic[_condition][stacktrace] = log;

			if (type == LogType.Log)
				numOfCollapsedLogs++;
			else if (type == LogType.Warning)
				numOfCollapsedLogsWarning++;
			else
				numOfCollapsedLogsError++;
		}

		if (type == LogType.Log)
			numOfLogs++;
		else if (type == LogType.Warning)
			numOfLogsWarning++;
		else
			numOfLogsError++;


		logs.Add(log);
		if (!collapse || isNew) {
			bool skip = false;
			if (log.logType == _LogType.Log && !showLog)
				skip = true;
			if (log.logType == _LogType.Warning && !showWarning)
				skip = true;
			if (log.logType == _LogType.Error && !showError)
				skip = true;
			if (log.logType == _LogType.Assert && !showError)
				skip = true;
			if (log.logType == _LogType.Exception && !showError)
				skip = true;

			if (!skip) {
				if (string.IsNullOrEmpty(filterText) || log.condition.ToLower().Contains(filterText.ToLower())) {
					currentLog.Add(log);
					newLogAdded = true;
				}
			}
		}

		if (newLogAdded) {
			calculateStartIndex();
			int totalCount = currentLog.Count;
			int totalVisibleCount = (int)(Screen.height * 0.75f / size.y);
			if (startIndex >= (totalCount - totalVisibleCount))
				scrollPosition.y += size.y;
		}

		try {
			// OnLog 是可选用户钩子（见 ReporterMessageReceiver，本身为空实现）。
			// 必须 DontRequireReceiver：默认 RequireReceiver 在接收者缺失时会对
			// 【每条日志】发一条 "no receiver" 警告，该警告又被本类日志回调捕获入队、
			// 下帧 flush 再触发警告……一次缺失即自我永动死循环（2026-10-14 把
			// 编辑器主线程刷死、Editor.log 膨胀 700MB+ 实测）。
			gameObject.SendMessage("OnLog", log, SendMessageOptions.DontRequireReceiver);
		}
		catch (System.Exception e) {
			Debug.LogException(e);
		}
	}

	List<Log> threadedLogs = new List<Log>();
	void CaptureLogThread(string condition, string stacktrace, LogType type)
	{
		Log log = new Log() { condition = condition, stacktrace = stacktrace, logType = (_LogType)type };
		lock (threadedLogs) {
			threadedLogs.Add(log);
		}
	}

#if !UNITY_CHANGE3
    class Scene
    {
    }
    class LoadSceneMode
    {
    }
    void OnLevelWasLoaded()
    {
        _OnLevelWasLoaded( null );
    }
#endif
    //new scene is loaded
    void _OnLevelWasLoaded( Scene _null1 , LoadSceneMode _null2 )
	{
		if (clearOnNewSceneLoaded)
			clear();

#if UNITY_CHANGE3
		currentScene = SceneManager.GetActiveScene().name ;
		Debug.Log( "Scene " + SceneManager.GetActiveScene().name + " is loaded");
#else
		currentScene = Application.loadedLevelName;
		Debug.Log("Scene " + Application.loadedLevelName + " is loaded");
#endif
	}

	//save user config
	void OnApplicationQuit()
	{
		PlayerPrefs.SetInt("Reporter_currentView", (int)currentView);
		PlayerPrefs.SetInt("Reporter_show", (show == true) ? 1 : 0);
		PlayerPrefs.SetInt("Reporter_collapse", (collapse == true) ? 1 : 0);
		PlayerPrefs.SetInt("Reporter_clearOnNewSceneLoaded", (clearOnNewSceneLoaded == true) ? 1 : 0);
		PlayerPrefs.SetInt("Reporter_showTime", (showTime == true) ? 1 : 0);
		PlayerPrefs.SetInt("Reporter_showScene", (showScene == true) ? 1 : 0);
		PlayerPrefs.SetInt("Reporter_showMemory", (showMemory == true) ? 1 : 0);
		PlayerPrefs.SetInt("Reporter_showFps", (showFps == true) ? 1 : 0);
		PlayerPrefs.SetInt("Reporter_showGraph", (showGraph == true) ? 1 : 0);
		PlayerPrefs.SetInt("Reporter_showLog", (showLog == true) ? 1 : 0);
		PlayerPrefs.SetInt("Reporter_showWarning", (showWarning == true) ? 1 : 0);
		PlayerPrefs.SetInt("Reporter_showError", (showError == true) ? 1 : 0);
		PlayerPrefs.SetString("Reporter_filterText", filterText);
		PlayerPrefs.SetFloat("Reporter_size", size.x);

		PlayerPrefs.SetInt("Reporter_showClearOnNewSceneLoadedButton", (showClearOnNewSceneLoadedButton == true) ? 1 : 0);
		PlayerPrefs.SetInt("Reporter_showTimeButton", (showTimeButton == true) ? 1 : 0);
		PlayerPrefs.SetInt("Reporter_showSceneButton", (showSceneButton == true) ? 1 : 0);
		PlayerPrefs.SetInt("Reporter_showMemButton", (showMemButton == true) ? 1 : 0);
		PlayerPrefs.SetInt("Reporter_showFpsButton", (showFpsButton == true) ? 1 : 0);
		PlayerPrefs.SetInt("Reporter_showSearchText", (showSearchText == true) ? 1 : 0);

		PlayerPrefs.Save();
	}

	//read build information 
	IEnumerator readInfo()
	{
		string prefFile = "build_info"; 
		string url = prefFile; 

		if (prefFile.IndexOf("://") == -1) {
			string streamingAssetsPath = Application.streamingAssetsPath;
			if (streamingAssetsPath == "")
				streamingAssetsPath = Application.dataPath + "/StreamingAssets/";
			url = System.IO.Path.Combine(streamingAssetsPath, prefFile);
		}

		//if (Application.platform != RuntimePlatform.OSXWebPlayer && Application.platform != RuntimePlatform.WindowsWebPlayer)
			if (!url.Contains("://"))
				url = "file://" + url;


		// float startTime = Time.realtimeSinceStartup;
#if UNITY_CHANGE4
		UnityWebRequest www = UnityWebRequest.Get(url);
		yield return www.SendWebRequest();
#else
		WWW www = new WWW(url);
		yield return www;
#endif

		if (!string.IsNullOrEmpty(www.error)) {
			Debug.LogError(www.error);
		}
		else {
#if UNITY_CHANGE4
			buildDate = www.downloadHandler.text;
#else
			buildDate = www.text;
#endif
		}

		yield break;
	}

    private void SaveLogsToDevice()
    {
        string filePath = Application.persistentDataPath + "/logs.txt";
        List<string> fileContentsList = new List<string>();
        Debug.Log("Saving logs to " + filePath);
        File.Delete(filePath);
        for (int i = 0; i < logs.Count; i++)
        {
            fileContentsList.Add(logs[i].logType + "\n" + logs[i].condition + "\n" + logs[i].stacktrace);
        }
        File.WriteAllLines(filePath, fileContentsList.ToArray());
    }
}


