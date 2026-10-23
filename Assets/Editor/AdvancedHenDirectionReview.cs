using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using AStar;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using Object = UnityEngine.Object;

namespace FTProject.EditorTools
{
    /// <summary>Isolated, single-prefab review. Never rebuilds the monster catalog or edits tables.</summary>
    [InitializeOnLoad]
    public static class AdvancedHenDirectionReview
    {
        public const string Output = "Docs/EnemyDirectionReview/AdvancedHen";
        private const string Prefab = "Assets/Prefabs/Enemy/Enemy_AdvancedHen.prefab";
        private const string SessionKey = "AdvancedHenDirectionReview.Start";
        private static BaseEnemy _demo;
        private static Camera _camera;
        private static int _corner, _lastFrame;
        private static readonly Vector2[] Corners = { new Vector2(-1.5f,-0.8f), new Vector2(-1.5f,0.8f), new Vector2(1.5f,0.8f), new Vector2(1.5f,-0.8f) };
        private static readonly List<string> Checks = new List<string>();

        static AdvancedHenDirectionReview()
        {
            EditorApplication.playModeStateChanged += OnPlay;
            EditorApplication.update += LiveTick;
        }

        [MenuItem("Tools/塔防/敌人方向示例/5. AdvancedHen 运行审核演示")]
        public static void StartDemo()
        {
            if (EditorApplication.isCompiling || EditorApplication.isPlayingOrWillChangePlaymode)
                throw new InvalidOperationException("Exit Play and wait for compilation first.");
            if (SceneManager.GetActiveScene().isDirty)
                throw new InvalidOperationException("Save your current scene before opening the isolated review.");
            Directory.CreateDirectory(Output);
            SessionState.SetString("AdvancedHenDirectionReview.PreviousScene", SceneManager.GetActiveScene().path);
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            SessionState.SetBool(SessionKey, true);
            EditorApplication.isPlaying = true;
        }

        private static void OnPlay(PlayModeStateChange state)
        {
            if (state == PlayModeStateChange.EnteredPlayMode && SessionState.GetBool(SessionKey, false))
            {
                SessionState.SetBool(SessionKey, false);
                _camera = MakeCamera(SceneManager.GetActiveScene(), false);
                _camera.orthographicSize = 3.1f;
                _camera.transform.position = new Vector3(0,1,-10);
                GameClock.Reset(); GameClock.SetPaused(false);
                _demo = Spawn(Vector2.up);
                _demo.name = "AdvancedHen - real BaseEnemy.Tick direction demo";
                _demo.transform.position = Corners[0];
                _corner = 1; Route(_demo, Corners[_corner]);
                Selection.activeGameObject = _demo.gameObject;
                Debug.Log("[AdvancedHenReview] Isolated Play demo ready. Use Game view; Tools direction review controls pause/speed. No tables or saved scenes modified.");
            }
            if (state == PlayModeStateChange.EnteredEditMode)
            {
                _demo = null; _camera = null;
                string previous = SessionState.GetString("AdvancedHenDirectionReview.PreviousScene", "");
                if (!string.IsNullOrEmpty(previous))
                {
                    SessionState.EraseString("AdvancedHenDirectionReview.PreviousScene");
                    EditorSceneManager.OpenScene(previous);
                }
            }
        }

        private static void LiveTick()
        {
            if (!_demo || !EditorApplication.isPlaying || EditorApplication.isPaused || Time.frameCount == _lastFrame) return;
            _lastFrame = Time.frameCount;
            _demo.Tick(GameClock.DeltaTime);
            if (Vector2.Distance(_demo.Position, Corners[_corner]) < 0.16f)
            {
                _corner = (_corner + 1) % Corners.Length;
                Route(_demo, Corners[_corner]);
            }
        }

        [MenuItem("Tools/塔防/敌人方向示例/6. AdvancedHen 暂停或继续")]
        public static void TogglePause() { if (_demo) GameClock.SetPaused(!GameClock.IsPaused); }
        [MenuItem("Tools/塔防/敌人方向示例/7. AdvancedHen 切换 1/2/3 倍速")]
        public static void CycleSpeed() { if (_demo) GameClock.Speed = GameClock.NextTier(GameClock.Speed); }
        [MenuItem("Tools/塔防/敌人方向示例/8. AdvancedHen 触发攻击")]
        public static void Attack() { if (_demo) _demo.TriggerAttackAnim(); }
        [MenuItem("Tools/塔防/敌人方向示例/9. AdvancedHen 运行检查")]
        public static void ChecksFromMenu() { Debug.Log(RunChecks()); }
        [MenuItem("Tools/塔防/敌人方向示例/10. AdvancedHen 采集四向静态图")]
        public static void ViewsFromMenu() { Debug.Log(CaptureViews()); }
        [MenuItem("Tools/塔防/敌人方向示例/11. AdvancedHen 采集行走转弯帧")]
        public static void MotionFromMenu() { Debug.Log(CaptureMotion()); }
        [MenuItem("Tools/塔防/敌人方向示例/12. AdvancedHen 采集攻击死亡复用帧")]
        public static void ActionsFromMenu() { Debug.Log(CaptureActions()); }

        public static EnemyConfig SampleConfig(bool flying = false, string controller = "Rooster")
        {
            // In-memory fixture, never written to Luban/ConfigJson/Gen.
            return new EnemyConfig(new cfg.EnemyData(990001, 1f, 10f, "AdvancedHen review", 0, 1000,
                "Enemy_AdvancedHen", 0f, 1, 1, 1f, 0.3f, flying ? 1 : 0, controller, "Isolated direction review"));
        }

        private static List<Point> Path(Vector2 start, Vector2 end)
        {
            return new List<Point> { new Point(0,0) { Center=start }, new Point(0,1) { Center=end } };
        }
        private static void Route(BaseEnemy enemy, Vector2 target) { enemy.SetPath(Path(enemy.Position, target)); }

        private static BaseEnemy Spawn(Vector2 direction, bool flying = false, string prefabPath = Prefab)
        {
            var go = Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath));
            foreach (var node in go.GetComponentsInChildren<Transform>(true)) node.gameObject.layer = 30;
            go.transform.position = Vector3.zero;
            var enemy = go.GetComponent<BaseEnemy>();
            enemy.Init(SampleConfig(flying, prefabPath == Prefab ? "Rooster" : ""), Path(Vector2.zero, direction * 50f));
            return enemy;
        }

        private static void Check(string name, bool pass)
        {
            Checks.Add((pass ? "PASS " : "FAIL ") + name);
        }

        public static string RunChecks()
        {
            RequireDemo();
            Checks.Clear();
            float speed = GameClock.Speed; bool paused = GameClock.IsPaused;
            GameClock.Speed = 1; GameClock.SetPaused(false);
            var e = Spawn(Vector2.up);
            var visual = e.GetComponent<EnemyDirectionalVisual>();
            var animator = e.GetComponent<Animator>();
            try
            {
                Check("Real complete profile and atlas references", visual && visual.IsConfigured);
                Check("R2 front/back wing occlusion config", visual.Profile.Down.WingsBehindBody && !visual.Profile.Up.WingsBehindBody);
                Check("Configured controller survives Rooster family config", animator.runtimeAnimatorController == visual.Profile.Controller);
                var expected = new[] { EnemyFacing.Up, EnemyFacing.Down, EnemyFacing.Left, EnemyFacing.Right };
                var directions = new[] { Vector2.up, Vector2.down, Vector2.left, Vector2.right };
                for (int d=0; d<4; d++)
                {
                    e.transform.position=Vector3.zero; Route(e, directions[d]*50);
                    Vector2 before=e.Position; e.Tick(0.1f);
                    Check("Actual movement and facing "+expected[d], visual.Facing == expected[d] && Vector2.Dot(e.Position-before,directions[d]) > 0.09f);
                    Check("Exactly one body view "+expected[d], visual.Head.enabled == (d<2) && visual.HorizontalRenderers.All(sr=>sr.enabled == (d>=2)));
                    Check("Positive world health bar X "+expected[d], e.transform.Find("HpBar").lossyScale.x > 0);
                    Check("No ground shadow "+expected[d], !e.GetComponentsInChildren<Transform>(true).Any(t=>t.name=="Shadow"));
                    if(d<2)
                    {
                        Check("Vertical clears root mirror "+expected[d], e.transform.localScale.x>0);
                        Check("Wing depth matches perspective "+expected[d], d==0 ? visual.WingL.sortingOrder>visual.Body.sortingOrder : visual.WingL.sortingOrder<visual.Body.sortingOrder);
                        Check("Leg roots overlap behind belly "+expected[d], visual.LegL.sortingOrder<visual.Body.sortingOrder && visual.LegL.bounds.max.y>visual.Body.bounds.min.y);
                        Check("Foot contact remains at actor origin "+expected[d], Mathf.Abs(Mathf.Min(visual.LegL.bounds.min.y,visual.LegR.bounds.min.y)-e.transform.position.y)<0.035f);
                    }
                    for(int i=0;i<3;i++)
                    {
                        e.gameObject.SendMessage("SetHead",i,SendMessageOptions.RequireReceiver);
                        var parts=d==0?visual.Profile.Up:visual.Profile.Down;
                        Check("Head event "+expected[d]+" expression "+i, visual.HeadIndex==i && (d>=2 || visual.Head.sprite==parts.HeadAt(i)));
                    }
                }
                e.Init(SampleConfig(),Path(e.Position,e.Position+Vector2.up*50));
                Check("Pooled reset normal head before first visible frame", visual.HeadIndex==0 && visual.Head.sprite==visual.Profile.Up.NormalHead);
                animator.Play("Walk",0,0.37f); animator.Update(0);
                float phase=animator.GetCurrentAnimatorStateInfo(0).normalizedTime;
                Route(e,e.Position+Vector2.right*50); Route(e,e.Position+Vector2.up*50);
                Check("Turn preserves locomotion state and phase", animator.GetCurrentAnimatorStateInfo(0).IsName("Walk") && Mathf.Abs(animator.GetCurrentAnimatorStateInfo(0).normalizedTime-phase)<0.001f);
                var last=visual.Facing; visual.Face(Vector2.zero);
                Check("Zero displacement keeps facing",visual.Facing==last);
                Check("Diagonal hysteresis keeps horizontal",EnemyDirectionalVisual.SelectFacing(new Vector2(1,1.1f),EnemyFacing.Left,true)==EnemyFacing.Right);
                Check("Diagonal hysteresis changes at dominant axis",EnemyDirectionalVisual.SelectFacing(new Vector2(1,1.3f),EnemyFacing.Right,true)==EnemyFacing.Up);
                Check("Diagonal hysteresis keeps vertical",EnemyDirectionalVisual.SelectFacing(new Vector2(1.1f,1),EnemyFacing.Up,true)==EnemyFacing.Up);
                var faceLeft=typeof(BaseEnemy).GetField("_artFaceLeft",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic);
                faceLeft.SetValue(e,false); Route(e,e.Position+Vector2.left*50);
                Check("ArtFaceLeft false mirrors left",e.transform.localScale.x<0);
                Route(e,e.Position+Vector2.up*50); Check("ArtFaceLeft false vertical clears mirror",e.transform.localScale.x>0);
                faceLeft.SetValue(e,true);
                foreach(var state in new[]{EnemyAnimState.Idle,EnemyAnimState.Ready,EnemyAnimState.Walk,EnemyAnimState.Run})
                {
                    e.SetAnimState(state); animator.Update(0.1f); animator.Update(0.1f);
                    Check("State contract "+state,animator.GetCurrentAnimatorStateInfo(0).IsName(state.ToString()) && visual.Head.enabled);
                }
                e.SetAnimSpeed(1.25f); Check("Speed float contract",Mathf.Approximately(animator.GetFloat("Speed"),1.25f)); e.SetAnimSpeed(1);
                e.SetAnimState(EnemyAnimState.Walk); animator.Update(0.1f);
                e.TriggerAttackAnim();
                bool angry=false,returned=false;
                for(int frame=0;frame<24;frame++)
                {
                    animator.Update(0.05f);
                    bool attack=animator.GetCurrentAnimatorStateInfo(0).IsName("Attack");
                    angry |= attack && visual.HeadIndex==1 && visual.Head.sprite==visual.Profile.Up.AngryHead;
                    returned |= angry && animator.GetCurrentAnimatorStateInfo(0).IsName("Walk") && visual.HeadIndex==0;
                }
                Check("Attack trigger enters attack with angry directional head",angry);
                Check("Attack completes and returns to walk with normal head",returned);
                float hp=e.CurrentHp;
                e.Hurt(2); Check("Hurt reduces HP and health fill",e.CurrentHp==hp-2 && e.transform.Find("HpBar/Fill").localScale.x<1);
                var block=new MaterialPropertyBlock(); visual.Head.GetPropertyBlock(block);
                Check("Hurt enables real white shader on all views",block.GetFloat("_FlashAmount")==1);
                e.Tick(0.09f); visual.Head.GetPropertyBlock(block); Check("Flash expires",block.GetFloat("_FlashAmount")==0);
                GameClock.Speed=3; e.Tick(0); Check("Animator follows 3x speed",animator.speed==3);
                Vector2 position=e.Position; e.Tick(0); Check("Zero delta does not move",e.Position==position);
                GameClock.Speed=1; e.Tick(0);
                e.SetAnimState(EnemyAnimState.Death); animator.Update(0.1f); animator.Update(0.1f);
                Check("Native death animation event keeps Up dead head",visual.HeadIndex==2 && visual.Head.sprite==visual.Profile.Up.DeadHead);
                e.SetAnimState(EnemyAnimState.Walk); animator.Rebind(); animator.Update(0);
                Route(e,e.Position+Vector2.right*50); e.Hurt(100);
                e.Tick(0.12f);
                visual.Head.GetPropertyBlock(block);
                Check("Lethal hit flash expires during death fade",block.GetFloat("_FlashAmount")==0);
                Check("Death fade and shrink cover vertical and horizontal renderers",!e.IsAlive && visual.Head.color.a<1 && visual.HorizontalRenderers.All(sr=>sr.color.a<1) && e.transform.localScale.x<0 && Mathf.Abs(e.transform.localScale.x)<0.5f);
                var pool=new ObjectPool<BaseEnemy>(()=>e,x=>x.OnRecycle()); pool.Release(e);
                var again=pool.Get(); again.transform.position=Vector3.zero; again.Init(SampleConfig(),Path(Vector2.zero,Vector2.down*50));
                Check("Pool returns same instance with Down normal head",again==e && visual.Facing==EnemyFacing.Down && visual.HeadIndex==0 && visual.Head.sprite==visual.Profile.Down.NormalHead);
                Check("Reused body opacity restored",visual.Head.color.a==1 && visual.HorizontalRenderers.All(sr=>sr.color.a==1));
                Check("Pool reuse never restores a shadow",!e.GetComponentsInChildren<Transform>(true).Any(t=>t.name=="Shadow"));
                e.OnRecycle(); e.Init(SampleConfig(true),Path(e.Position,e.Position+Vector2.up*50));
                Check("Flying straight vertical spawn",visual.Facing==EnemyFacing.Up); position=e.Position;e.Tick(0.1f);
                Check("Flying moves Up",e.Position.y>position.y);
                var legacy=Spawn(Vector2.up,false,"Assets/Prefabs/Enemy/Enemy_Bat.prefab");
                try
                {
                    Check("Unconfigured Bat has no directional component",legacy.GetComponent<EnemyDirectionalVisual>()==null);
                    legacy.SetPath(new List<Point>{new Point(0,0){Center=Vector2.zero},new Point(0,1){Center=Vector2.up*3},new Point(1,1){Center=Vector2.up*3+Vector2.right*3}});
                    float x=legacy.transform.localScale.x; legacy.Tick(0.1f);
                    Check("Legacy look-ahead and vertical mirror retained",x<0 && legacy.transform.localScale.x==x && legacy.Position.y>0);
                }
                finally { Object.DestroyImmediate(legacy.gameObject); }
            }
            finally
            {
                Object.DestroyImmediate(e.gameObject); GameClock.Speed=speed;GameClock.SetPaused(paused);
                File.WriteAllText(Output+"/actual_runtime_checks.txt","Real art, isolated Unity Play Mode, "+Application.unityVersion+"\n"+string.Join("\n",Checks));
            }
            return "Checks="+Checks.Count+", failures="+Checks.Count(x=>x.StartsWith("FAIL"));
        }

        private static Camera MakeCamera(Scene scene, bool transparent)
        {
            var go=new GameObject("AdvancedHen review camera"); SceneManager.MoveGameObjectToScene(go,scene);
            var camera=go.AddComponent<Camera>(); camera.scene=scene; camera.orthographic=true;
            camera.transform.position=new Vector3(0,0.9f,-10); camera.orthographicSize=1.35f;
            camera.clearFlags=CameraClearFlags.SolidColor;
            camera.backgroundColor=transparent?Color.clear:new Color(0.16f,0.19f,0.15f,1);
            camera.cullingMask=1<<30;
            return camera;
        }

        private static void Render(Camera camera,string path,int size=512)
        {
            var target=RenderTexture.GetTemporary(size,size,24,RenderTextureFormat.ARGB32);
            var previous=RenderTexture.active;
            var image=new Texture2D(size,size,TextureFormat.RGBA32,false);
            try
            {
                camera.targetTexture=target; camera.Render(); RenderTexture.active=target;
                image.ReadPixels(new Rect(0,0,size,size),0,0); image.Apply();
                Directory.CreateDirectory(System.IO.Path.GetDirectoryName(path)); File.WriteAllBytes(path,image.EncodeToPNG());
            }
            finally { camera.targetTexture=null;RenderTexture.active=previous;RenderTexture.ReleaseTemporary(target);Object.DestroyImmediate(image); }
        }

        public static string CaptureReference()
        {
            var scene=EditorSceneManager.NewPreviewScene();
            try
            {
                var root=(GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(Prefab),scene);
                foreach(var t in root.GetComponentsInChildren<Transform>(true))t.gameObject.layer=30;
                root.transform.Find("HpBar").gameObject.SetActive(false);
                var camera=MakeCamera(scene,true);
                Render(camera,Output+"/reference_current.png");
                var sprites=root.GetComponentsInChildren<SpriteRenderer>();
                var bounds=new Bounds(); bool first=true;
                foreach(var sr in sprites)if(sr.enabled && sr.name!="Shadow") {if(first){bounds=sr.bounds;first=false;}else bounds.Encapsulate(sr.bounds);}
                return "Current original bounds: "+bounds.ToString()+"; reference_current.png";
            }
            finally { EditorSceneManager.ClosePreviewScene(scene); }
        }

        public static string CaptureViews()
        {
            RequireDemo();
            // Runtime Animator evaluation/events are disabled in preview scenes. Capture in Play.
            var scene=SceneManager.GetActiveScene();
            _demo.gameObject.SetActive(false);
            var camera=MakeCamera(scene,false);
            BaseEnemy enemy=null;
            try
            {
                enemy=Spawn(Vector2.left);
                var animator=enemy.GetComponent<Animator>();
                var dirs=new[]{Vector2.left,Vector2.right,Vector2.up,Vector2.down};
                var names=new[]{"Left","Right","Up","Down"};
                var bounds=new List<string>();
                for(int i=0;i<4;i++)
                {
                    enemy.transform.position=Vector3.zero;Route(enemy,dirs[i]*50);
                    animator.Play("Walk",0,0);animator.Update(0);
                    Render(camera,Output+"/view_"+names[i]+".png");
                    var body=enemy.GetComponentsInChildren<SpriteRenderer>().Where(sr=>sr.enabled && sr.name!="Shadow" && !sr.transform.IsChildOf(enemy.transform.Find("HpBar"))).ToArray();
                    var b=body[0].bounds;foreach(var sr in body)b.Encapsulate(sr.bounds);
                    bounds.Add(names[i]+" "+b.ToString());
                }
                File.WriteAllText(Output+"/view_bounds.txt",string.Join("\n",bounds));
                return "Captured four real Unity directions.";
            }
            finally
            {
                if(enemy) Object.DestroyImmediate(enemy.gameObject);
                Object.DestroyImmediate(camera.gameObject); _demo.gameObject.SetActive(true);
            }
        }

        public static string CaptureMotion()
        {
            RequireDemo();
            var scene=SceneManager.GetActiveScene();
            _demo.gameObject.SetActive(false);
            var camera=MakeCamera(scene,false);
            BaseEnemy e=null;
            float previousSpeed=GameClock.Speed;GameClock.Speed=1;
            try
            {
                e=Spawn(Vector2.up);
                camera.orthographicSize=2.4f;camera.transform.position=new Vector3(0,1f,-10);
                var animator=e.GetComponent<Animator>();
                Vector2[] corners={new Vector2(-0.7f,-0.5f),new Vector2(-0.7f,0.5f),new Vector2(0.7f,0.5f),new Vector2(0.7f,-0.5f)};
                e.transform.position=corners[0];int next=1;Route(e,corners[next]);
                for(int i=0;i<180;i++)
                {
                    e.Tick(0.05f);animator.Update(0.05f);
                    if(Vector2.Distance(e.Position,corners[next])<0.12f){next=(next+1)%4;Route(e,corners[next]);}
                    Render(camera,Output+"/frames/turn_"+i.ToString("D3")+".png",320);
                }
                return "180 Unity-rendered motion frames at 20 fps.";
            }
            finally
            {
                if(e) Object.DestroyImmediate(e.gameObject);
                GameClock.Speed=previousSpeed;Object.DestroyImmediate(camera.gameObject);_demo.gameObject.SetActive(true);
            }
        }

        public static string CaptureActions()
        {
            RequireDemo();
            _demo.gameObject.SetActive(false);
            var camera=MakeCamera(SceneManager.GetActiveScene(),false);
            camera.orthographicSize=1.95f;camera.transform.position=new Vector3(0.5f,0.7f,-10);
            float speed=GameClock.Speed;GameClock.Speed=1;
            var report=new List<string>();
            BaseEnemy e=null;
            try
            {
                for(int d=0;d<2;d++)
                {
                    var direction=d==0?Vector2.up:Vector2.down;
                    e=Spawn(direction);
                    var visual=e.GetComponent<EnemyDirectionalVisual>();var animator=e.GetComponent<Animator>();
                    e.SetPath(null);animator.Play("Walk",0,0);animator.Update(0);e.TriggerAttackAnim();
                    bool angry=false,dead=false,recycled=false,same=false;
                    for(int i=0;i<64;i++)
                    {
                        if(i==24)e.Hurt(2);
                        if(i==32)e.Hurt(100);
                        if(i==47)
                        {
                            recycled=e.IsFullyRecycled && !e.gameObject.activeSelf;
                            // Access the existing manager pool only in this isolated editor review.
                            var method=typeof(EnemyManager).GetMethod("GetPool",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic);
                            var pool=(ObjectPool<BaseEnemy>)method.Invoke(EnemyManager.Instance,new object[]{"Enemy_AdvancedHen"});
                            var again=pool.Get();same=again==e;
                            if(!same) throw new InvalidOperationException("Expected the same automatically recycled example instance.");
                            e.transform.position=Vector3.zero;e.Init(SampleConfig(),Path(Vector2.zero,direction*50));e.SetPath(null);
                        }
                        if(e.gameObject.activeSelf)
                        {
                            e.Tick(0.05f);animator.Update(0.05f);
                            angry|=visual.HeadIndex==1;dead|=i>=32 && i<47 && visual.HeadIndex==2;
                        }
                        Render(camera,Output+"/frames/action_"+(d*64+i).ToString("D3")+".png",320);
                    }
                    report.Add((d==0?"Up":"Down")+" native attack angry="+angry+"; native death head="+dead+
                        "; EnemyManager auto-recycled="+recycled+"; same pooled instance="+same+"; normal after reuse="+(visual.HeadIndex==0));
                    Object.DestroyImmediate(e.gameObject);e=null;
                }
                File.WriteAllLines(Output+"/action_pool_checks.txt",report);
                return string.Join("\n",report);
            }
            finally
            {
                if(e) Object.DestroyImmediate(e.gameObject);
                GameClock.Speed=speed;Object.DestroyImmediate(camera.gameObject);_demo.gameObject.SetActive(true);
            }
        }

        [MenuItem("Tools/塔防/敌人方向示例/13. AdvancedHen 采集上下行走循环")]
        public static void LoopsFromMenu() { Debug.Log(CaptureLoops()); }

        public static string CaptureLoops()
        {
            RequireDemo(); _demo.gameObject.SetActive(false);
            var camera=MakeCamera(SceneManager.GetActiveScene(),false);
            float speed=GameClock.Speed;GameClock.Speed=1;
            BaseEnemy e=null;
            try
            {
                for(int d=0;d<2;d++)
                {
                    e=Spawn(d==0?Vector2.up:Vector2.down);e.SetPath(null);
                    e.transform.Find("HpBar").gameObject.SetActive(false);
                    var animator=e.GetComponent<Animator>();animator.Play("Walk",0,0);animator.Update(0);
                    for(int i=0;i<10;i++)
                    {
                        Render(camera,Output+"/frames/loop_"+(d==0?"Up_":"Down_")+i.ToString("D2")+".png",512);
                        e.Tick(0.05f);animator.Update(0.05f);
                    }
                    Object.DestroyImmediate(e.gameObject);e=null;
                }
                return "Two real 0.5 second walk cycles, 10 frames per direction at 20 fps.";
            }
            finally
            {
                if(e)Object.DestroyImmediate(e.gameObject);
                GameClock.Speed=speed;Object.DestroyImmediate(camera.gameObject);_demo.gameObject.SetActive(true);
            }
        }

        private static void RequireDemo()
        {
            if(!Application.isPlaying || !_demo)
                throw new InvalidOperationException("Start the isolated AdvancedHen review demo first.");
        }

        public static string PauseSnapshot()
        {
            if(!_demo)throw new InvalidOperationException("Review demo is not running.");
            return _demo.Position+" | "+_demo.GetComponent<Animator>().GetCurrentAnimatorStateInfo(0).normalizedTime.ToString("F5")+" | paused="+GameClock.IsPaused+" | speed="+GameClock.Speed;
        }
    }
}
