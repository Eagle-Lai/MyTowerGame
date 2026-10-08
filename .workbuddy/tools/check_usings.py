"""
命名空间引用校验。

覆盖最常见的一类"API 存在但编译报错"：使用了某个类型却没 import 它的命名空间
→ CS0246 "The type or namespace name 'X' could not be found"。

做法：维护"Unity 类型 → 命名空间"映射，扫描每个源码文件里出现的类型名，
      检查该文件是否 import 了对应命名空间（或写了全限定名）。
"""
import io, os, re, sys, collections

# ★ ROOT 由脚本自身位置推导，避免硬编码路径写错后"扫 0 个文件却 PASS"
_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(os.path.dirname(os.path.dirname(_HERE)), 'Assets')
DIRS = [os.path.join(ROOT, 'Scripts'), os.path.join(ROOT, 'Editor'), os.path.join(ROOT, 'Gen')]

# 类型名 -> 命名空间
NS = {}
def reg(ns, names):
    for n in names.split():
        NS[n] = ns

reg('UnityEngine', """
GameObject Transform Component MonoBehaviour Object Behaviour Renderer SpriteRenderer Sprite Texture2D Texture
Color Color32 ColorBlock_placeholder Bounds Rect RectInt Mathf Debug Time Application Resources Font Camera Screen
Vector2 Vector3 Vector4 Quaternion Animator Canvas CanvasGroup RectTransform CanvasRenderer RectTransformUtility
Collider Collider2D Rigidbody Rigidbody2D Joint Joint2D CharacterController Physics Physics2D LineRenderer
TextureFormat TextureWrapMode FilterMode HideFlags Coroutine WaitForEndOfFrame WaitForSeconds AsyncOperation
TextAnchor HorizontalWrapMode VerticalWrapMode RuntimeAnimatorController AnimationClip ScriptableObject
LayerMask Space KeyCode Input Random Material Shader ParticleSystem AudioSource AudioClip
GUILayout
""")
# ColorBlock 实际在 UnityEngine.UI
NS.pop('ColorBlock_placeholder', None)

reg('UnityEngine.UI', 'Image Text Button CanvasScaler GraphicRaycaster Outline Shadow ColorBlock Selectable Graphic MaskableGraphic ScrollRect LayoutGroup GridLayoutGroup ContentSizeFitter InputField Toggle Slider Scrollbar Dropdown RawImage')
reg('UnityEngine.EventSystems', 'EventSystem StandaloneInputModule PointerEventData BaseEventData UIBehaviour ExecuteEvents')
reg('UnityEngine.SceneManagement', 'Scene SceneManager LoadSceneMode SceneUtility')
reg('UnityEngine.Rendering', 'SortingGroup GraphicsSettings')
reg('UnityEngine.Networking', 'UnityWebRequest DownloadHandlerAssetBundle UnityWebRequestAssetBundle UnityWebRequestAsyncOperation')
reg('UnityEditor', """
AssetDatabase AssetImporter PrefabUtility EditorUtility Selection PlayerSettings EditorBuildSettings
EditorBuildSettingsScene EditorUserBuildSettings BuildPipeline BuildAssetBundleOptions BuildTarget
SerializedObject SerializedProperty MenuItem UIOrientation TextureImporter TextureImporterType SpriteImportMode
TextureImporterCompression ImportAssetOptions ObjectFactory EditorApplication EditorGUI EditorGUILayout
AssetDatabaseLoadOperation PrefabAssetType EditorPrefs BuildTargetGroup
EditorWindow EditorStyles MessageType
""")
reg('UnityEditor.Build', 'NamedBuildTarget')
reg('UnityEditor.SceneManagement', 'EditorSceneManager OpenSceneMode NewSceneSetup NewSceneMode PrefabStage')
reg('System', 'Action Func Exception IEnumerator IDisposable DateTime TimeSpan StringComparer Nullable')
reg('System.Collections', 'IEnumerator ArrayList Hashtable')
reg('System.Collections.Generic', 'List Dictionary HashSet Queue Stack KeyValuePair IList IEnumerable ICollection IDictionary')
reg('System.IO', 'File Directory Path StreamReader StreamWriter MemoryStream FileStream')
reg('System.Text', 'StringBuilder Encoding')
reg('TMPro', """
TMP_Text TextMeshProUGUI TextMeshPro TMP_FontAsset TMP_SpriteAsset TMP_Settings TMP_InputField
TMP_Dropdown TextAlignmentOptions TextOverflowModes FontStyles FontWeight TextWrappingModes
ShaderUtilities TMP_TextInfo TMP_CharacterInfo TMP_UpdateManager
""")
reg('SimpleJSON', 'JSONNode JSONArray JSONObject JSONString JSONNumber JSONBool JSONNull')
reg('SimpleJSON', 'JSONNode JSONArray JSONObject JSONString JSONNumber JSONBool JSONNull')
reg('cfg', 'EnemyData TowerInfo BulletData Global LevelMap RoundData SceneInfo EnemyList EnemyDataList TowerInfoList BulletDataList LevelMapList GlobalList SceneInfoList RoundDataList EnemyListList Tables')
reg('cfg.item', 'Item TbItem ItemExchange')
reg('AStar', 'Point AStarWrapper Singleton')
reg('FTProject', """
Configs ResLoader ResTable ResBundle ResAddress ResPathUtil EditorResLoader BundleResLoader ResLoaderRunner
ResLoaderRunnerBehaviour IResLoader YooAssetResLoader EventDispatcher EventName ObjectPool TimerManager BaseManager IManagerInterface
PlayerDataManager CombatSystem EnemyGrid BaseEnemy EnemyManager BaseBullet BulletManager BulletState BaseTower
NormalTower TowerManager TowerConfig TowerType TargetMode TowerPlacement LevelConfig LevelMapConfig RoundConfig
WaveGroupConfig EnemyConfig BulletConfig GlobalConfig WaveManager GameFlowManager GameFlowState BoardView CellView
CellData CellType CellHighlight BoardGeometry BoardSorting PathArrowView Launcher GameSceneLauncher UIManager
UILayout HudView TipsView CameraController EnemyType EnemyAnimState AStarManager
""")
reg('FTProject.EditorTools', 'FTBundlePackRule FTYooAssetDefine FTYooAssetSetupWizard')
# YooAsset 3.0.6（UPM 包）：运行时程序集 YooAsset / 编辑器程序集 YooAsset.Editor
reg('YooAsset', 'EBundleType EFileNameStyle PackageBuildResult EditorSimulateBuildInvoker')
reg('YooAsset.Editor', """
IBundlePackRule BundlePackRuleData BundlePackRuleResult DisplayName DisplayNameAttribute
DefaultBundlePackRule BundleCollectorSetting BundleCollectorSettingData BundleCollectorPackage
BundleCollectorGroup BundleCollector ECollectorType AddressByFileName CollectAll NormalIgnoreRule
EnableGroup DisableGroup BundleSimulateBuilder ScriptableBuildPipeline ScriptableBuildParameters
BuildResult BuildParameters EBuildPipeline EBundledCopyOption ECompressOption BundleBuilderHelper
CollectResult CollectAssetInfo EditorAssetInfo
""")


def strip_comments_and_strings(src):
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c == '/' and i + 1 < n and src[i + 1] == '/':
            while i < n and src[i] != '\n':
                i += 1
            continue
        if c == '/' and i + 1 < n and src[i + 1] == '*':
            i += 2
            while i + 1 < n and not (src[i] == '*' and src[i + 1] == '/'):
                i += 1
            i += 2
            continue
        if c == '@' and i + 1 < n and src[i + 1] == '"':
            i += 2
            while i < n:
                if src[i] == '"':
                    if i + 1 < n and src[i + 1] == '"':
                        i += 2
                        continue
                    i += 1
                    break
                i += 1
            continue
        if c == '"':
            i += 1
            while i < n:
                if src[i] == '\\':
                    i += 2
                    continue
                if src[i] == '"':
                    i += 1
                    break
                i += 1
            continue
        if c == "'":
            i += 1
            while i < n:
                if src[i] == '\\':
                    i += 2
                    continue
                if src[i] == "'":
                    i += 1
                    break
                i += 1
            continue
        out.append(c)
        i += 1
    return ''.join(out)


files = []
for d in DIRS:
    if not os.path.isdir(d):
        continue
    for dp, _, fns in os.walk(d):
        for fn in fns:
            if fn.endswith('.cs'):
                files.append(os.path.join(dp, fn))
files.sort()

# ★ 自检：一个 .cs 都没扫到，说明 ROOT 写错了，必须 FAIL —— 不能沉默地报 PASS
if not files:
    print('目录下没扫到任何 .cs 文件，ROOT 很可能写错了：')
    for d in DIRS:
        print('    %s%s' % (d, '' if os.path.isdir(d) else '   <- 该目录不存在'))
    print('RESULT: FAIL (扫描到 0 个文件)')
    sys.exit(1)
print('扫描 %d 个 .cs 文件' % len(files))

problems = []
for f in files:
    rel = os.path.relpath(f, ROOT)
    raw = io.open(f, encoding='utf-8-sig', errors='replace').read()
    code = strip_comments_and_strings(raw)

    # 该文件声明的类型（自身定义的不需要 import）
    own = set(re.findall(
        r'\b(?:class|struct|enum|interface)\s+([A-Za-z_]\w*)', code))
    # 该文件声明的成员名（字段/属性/方法/参数）——它们只是"名字"，
    # 不是类型引用。漏掉这一步会把 `public string Text { ... }`
    # 这类属性名误判成用了 UnityEngine.UI.Text。
    own |= set(re.findall(
        r'\b(?:public|private|protected|internal)\s+(?:static\s+|readonly\s+|const\s+|override\s+|virtual\s+|abstract\s+|sealed\s+)*'
        r'[\w\<\>\[\]\.,\s]+?\s+([A-Za-z_]\w*)\s*(?:[;=]|\{|\()', code))
    own |= set(re.findall(r'\b(\w+)\s*\{', code))

    own |= set(re.findall(r'\b([A-Za-z_]\w*)\s*;', code))

    # using 指令
    usings = set(re.findall(r'\busing\s+([\w\.]+)\s*;', code))
    # 也把当前 namespace 视作已导入（同命名空间内的类型无需 using）
    cur_ns = re.findall(r'\bnamespace\s+([\w\.]+)', code)
    usings |= set(cur_ns)
    # 父命名空间也算可见
    for ns in list(cur_ns):
        parts = ns.split('.')
        for i in range(1, len(parts)):
            usings.add('.'.join(parts[:i]))

    used_ns = collections.defaultdict(set)   # 需要的 ns -> 用到的类型
    for name, ns in NS.items():
        if name in own:
            continue
        if re.search(r'(?<![\w\.])' + re.escape(name) + r'(?![\w])', code):
            used_ns[ns].add(name)

    for ns, names in sorted(used_ns.items()):
        if ns in usings:
            continue
        problems.append((rel, ns, sorted(names)))

print('=' * 78)
print('命名空间引用校验（缺失 → CS0246）')
if problems:
    for rel, ns, names in problems:
        print('  FAIL  %s' % rel)
        print('        使用了 %s 里的类型，但未 import 该命名空间：' % ns)
        print('          %s' % ', '.join(names))
        print('        修复：在文件顶部加 `using %s;`' % ns)
else:
    print('  PASS  所有用到的类型都能通过现有 using 解析')
print()
print('RESULT:', 'FAIL' if problems else 'PASS')
sys.exit(1 if problems else 0)
