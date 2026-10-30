using System;

using System.Collections.Generic;

using System.IO;

using System.Linq;

using System.Reflection;

using AStar;

using UnityEditor;

using UnityEditor.SceneManagement;

using UnityEngine;

using UnityEngine.SceneManagement;

using Object = UnityEngine.Object;



namespace FTProject.EditorTools

{

    // Single installed-prefab review in a real, unsaved Play scene. No manual Animator.Update

    // is used for media or time/event observations. Each record carries the actual Unity frame.

    [InitializeOnLoad]

    public static class EnemyDirectionBatchReview

    {

        private const string RequestKey = "EnemyDirectionBatchReview.Request";

        private const string RestoreKey = "EnemyDirectionBatchReview.Restore";

        private const string Root = "Docs/EnemyDirectionReview/Batch01_10";

        [Serializable] private sealed class Request { public string name, revision; public bool deathUp; }

        [Serializable] private sealed class SavedScene { public string path; public bool loaded, active; }

        [Serializable] private sealed class SavedScenes { public SavedScene[] scenes; }

        [Serializable] private sealed class Observation

        {

            public string stage, state, facing, file;

            public int frame, expression;

            public double realtime;

            public float unscaledDelta, simulationDelta, speed, normalizedTime, hp, alpha, flash;

            public Vector3 position, scale;

            public bool alive, recycled, paused, headAngry, shadow;

        }

        private static Request _request;

        private static string _out;

        private static BaseEnemy _enemy;

        private static EnemyDirectionalVisual _visual;

        private static Animator _animator;

        private static SpriteRenderer[] _body;

        private static Camera _camera;

        private static RenderTexture _target;

        private static Texture2D _readback;

        private static StreamWriter _frames;

        private static readonly List<string> Checks = new List<string>();

        private static int _stage, _lastFrame, _stageFrames, _captureIndex;

        private static int _attackLeg;

        private static float _attackLegStart;

        private static double _stageStart, _nextCapture;

        private static float _scaledTime, _phaseStart;

        private static Vector2 _positionStart;

        private static bool _angry, _returned, _deadHead, _faded, _flashExpired, _pauseBaseline;

        private static float _rootScale;

        private static Vector2 _cameraOffset;

        private static float _cameraHalfSize;

        private static readonly Vector2[] Directions = { Vector2.up, Vector2.down, Vector2.left, Vector2.right };

        private static readonly string[] StageNames = { "UpWalk", "DownWalk", "LeftWalk", "RightWalk", "Idle", "Ready", "Walk", "Run", "Attack", "Hurt", "DeathAutoRecycle", "Reuse", "Pause", "Resume1x", "Speed2x", "Speed3x", "ContinuousTurns", "Flying", "Done" };

        public static bool Running { get { return !string.IsNullOrEmpty(SessionState.GetString(RequestKey, "")); } }



        static EnemyDirectionBatchReview()

        {

            EditorApplication.playModeStateChanged += OnMode;

            EditorApplication.update += Update;

        }



        public static void Start(string name, string revision, bool deathUp = false)

        {

            EnemyDirectionSpec spec;

            if (!EnemyDirectionPrefabBuilder.TryGetSpec(name, out spec) || (name != "AdvancedHen" && !spec.UseSeparateViewRigs))

                throw new InvalidOperationException("Only the approved example and this authorized batch can be reviewed.");

            if (string.IsNullOrEmpty(revision) || revision.Any(c => !char.IsLetterOrDigit(c) && c != '_'))

                throw new ArgumentException("Use a unique simple evidence revision.");

            if (Running || BalancePlayModeVerifier.Running || GameClock.IsManualSimulation || EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling || EditorUtility.scriptCompilationFailed)

                throw new InvalidOperationException("Review requires the explicitly handed-over, idle editor.");

            var saved = EditorSceneManager.GetSceneManagerSetup();

            for (int i=0;i<SceneManager.sceneCount;i++)

                if (SceneManager.GetSceneAt(i).isDirty || string.IsNullOrEmpty(SceneManager.GetSceneAt(i).path))

                    throw new InvalidOperationException("Save all open scenes before the isolated review.");

            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(spec.PrefabPath);

            if (!prefab || !prefab.GetComponent<EnemyDirectionalVisual>() || !prefab.GetComponent<EnemyDirectionalVisual>().IsConfigured)

                throw new InvalidOperationException("Final real directional prefab is not installed.");

            string output=Root+"/"+name+"/"+revision;

            if (Directory.Exists(output)) throw new InvalidOperationException("Evidence directory already exists; use a new revision.");

            Directory.CreateDirectory(output+"/frames");

            var setup = new SavedScenes { scenes=saved.Select(s=>new SavedScene{path=s.path,loaded=s.isLoaded,active=s.isActive}).ToArray() };

            SessionState.SetString(RestoreKey,JsonUtility.ToJson(setup));

            SessionState.SetString(RequestKey,JsonUtility.ToJson(new Request{name=name,revision=revision,deathUp=deathUp}));

            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);

            EditorApplication.isPlaying=true;

        }



        private static void OnMode(PlayModeStateChange state)

        {

            if (state==PlayModeStateChange.EnteredPlayMode && Running)

            {

                try { Begin(); } catch(Exception error) { Fail(error); }

            }

            if (state==PlayModeStateChange.EnteredEditMode && !string.IsNullOrEmpty(SessionState.GetString(RestoreKey,"")))

            {

                CloseFiles();

                var saved=JsonUtility.FromJson<SavedScenes>(SessionState.GetString(RestoreKey,""));

                SessionState.EraseString(RequestKey);SessionState.EraseString(RestoreKey);

                _enemy=null;_camera=null;

                EditorSceneManager.RestoreSceneManagerSetup(saved.scenes.Select(s=>new SceneSetup{path=s.path,isLoaded=s.loaded,isActive=s.active}).ToArray());

                Debug.Log("[EnemyDirectionBatchReview] Returned Unity with the saved scene setup restored.");

            }

        }



        private static EnemyConfig Config(string name,bool flying=false)

        {

            EnemyDirectionSpec spec;EnemyDirectionPrefabBuilder.TryGetSpec(name,out spec);

            string family=spec==null?"":new DirectoryInfo(Path.GetDirectoryName(spec.ControllerSource)).Name;

            return new EnemyConfig(new cfg.EnemyData(990001,1f,20f,name+" isolated direction review",0,1000,"Enemy_"+name,0f,1,1,1f,.3f,flying?1:0,family,"In-memory only; never exported",1));

        }



        private static List<Point> PathTo(Vector2 start,Vector2 end)

        { return new List<Point>{new Point(0,0){Center=start},new Point(0,1){Center=end}}; }

        private static void Route(Vector2 direction)

        { _enemy.SetPath(PathTo(_enemy.Position,_enemy.Position+direction*1000)); }

        private static bool NoShadow(BaseEnemy e)

        { return !e.GetComponentsInChildren<Transform>(true).Any(t=>t.name=="Shadow"); }

        private static float Flash(SpriteRenderer sr)

        { var block=new MaterialPropertyBlock();sr.GetPropertyBlock(block);return block.GetFloat("_FlashAmount"); }

        private static void Check(string name,bool pass)

        { Checks.Add((pass?"PASS ":"FAIL ")+name); }

        private static bool Visible(SpriteRenderer sr)

        { return sr && sr.enabled && !sr.forceRenderingOff && sr.gameObject.activeInHierarchy; }



        private static void Begin()

        {

            _request=JsonUtility.FromJson<Request>(SessionState.GetString(RequestKey,""));

            _out=Root+"/"+_request.name+"/"+_request.revision;

            Checks.Clear();GameClock.Reset();GameClock.Speed=1;GameClock.SetPaused(false);

            var prefab=AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Prefabs/Enemy/Enemy_"+_request.name+".prefab");

            _enemy=Object.Instantiate(prefab).GetComponent<BaseEnemy>();

            _enemy.transform.position=Vector3.zero;

            _enemy.Init(Config(_request.name,_request.name=="Bat"),PathTo(Vector2.zero,Vector2.up*1000));

            _visual=_enemy.GetComponent<EnemyDirectionalVisual>();_animator=_enemy.GetComponent<Animator>();

            var hp=_enemy.transform.Find("HpBar");

            _body=_enemy.GetComponentsInChildren<SpriteRenderer>(true).Where(sr=>!hp||!sr.transform.IsChildOf(hp)).ToArray();

            _rootScale=Mathf.Abs(_enemy.transform.localScale.x);

            var cameraBounds=_body[0].bounds;

            foreach(var sr in _enemy.GetComponentsInChildren<SpriteRenderer>(true))if(sr.sprite)cameraBounds.Encapsulate(sr.bounds);

            _cameraOffset=(Vector2)cameraBounds.center-_enemy.Position;

            _cameraHalfSize=Mathf.Max(.8f,cameraBounds.extents.magnitude*1.15f);

            _camera=new GameObject("Direction batch isolated review camera").AddComponent<Camera>();

            _camera.orthographic=true;_camera.clearFlags=CameraClearFlags.SolidColor;_camera.backgroundColor=new Color(.16f,.19f,.15f,1);

            _target=new RenderTexture(768,768,24,RenderTextureFormat.ARGB32);_target.Create();_camera.targetTexture=_target;

            _readback=new Texture2D(768,768,TextureFormat.RGBA32,false);

            _frames=new StreamWriter(_out+"/actual_frames.jsonl",false);

            _lastFrame=-1;_captureIndex=0;

            StaticChecks();EnterStage(0);

            Selection.activeGameObject=_enemy.gameObject;

        }



        private static void StaticChecks()

        {

            Check("Final installed complete directional profile",_visual.IsConfigured);

            Check("Profile controller retained through family-config Init",_animator.runtimeAnimatorController==_visual.Profile.Controller);

            Check("Ground shadow node removed",NoShadow(_enemy));

            var receiver=_enemy.GetComponent<MonsterAnimEventReceiver>();

            Check("Original event receiver and side head references preserved",receiver&&receiver.HeadRenderer&&receiver.HeadSprites!=null&&receiver.HeadSprites.Length>=3);

            foreach(var direction in Directions)

            {

                Route(direction);

                for(int expression=0;expression<3;expression++)

                {

                    _enemy.gameObject.SendMessage("SetHead",expression,SendMessageOptions.RequireReceiver);

                    bool vertical=_visual.Facing==EnemyFacing.Up||_visual.Facing==EnemyFacing.Down;

                    var parts=_visual.Facing==EnemyFacing.Up?_visual.Profile.Up:_visual.Profile.Down;

                    Check("SetHead delivery "+_visual.Facing+" "+expression,_visual.HeadIndex==expression&&(!vertical||_visual.Head.sprite==parts.HeadAt(expression))&&receiver.HeadRenderer.sprite==receiver.HeadSprites[expression]);

                }

            }

            _enemy.gameObject.SendMessage("SetHead",0,SendMessageOptions.RequireReceiver);

            foreach(var expected in new[]{new KeyValuePair<string,AnimatorControllerParameterType>("State",AnimatorControllerParameterType.Int),new KeyValuePair<string,AnimatorControllerParameterType>("Speed",AnimatorControllerParameterType.Float),new KeyValuePair<string,AnimatorControllerParameterType>("Attack",AnimatorControllerParameterType.Trigger),new KeyValuePair<string,AnimatorControllerParameterType>("Action",AnimatorControllerParameterType.Bool)})

                Check("Animator parameter "+expected.Key,_animator.parameters.Any(p=>p.name==expected.Key&&p.type==expected.Value));

            _animator.SetFloat("Speed",1.25f);Check("Speed float writable",Mathf.Approximately(_animator.GetFloat("Speed"),1.25f));_animator.SetFloat("Speed",1);

            var duplicates=new List<Point>{new Point(0,0){Center=Vector2.zero},new Point(0,0){Center=Vector2.zero},new Point(0,0){Center=Vector2.up*.0001f},new Point(0,1){Center=Vector2.up*5},new Point(1,1){Center=Vector2.up*5+Vector2.right*5}};

            _enemy.Init(Config(_request.name,false),duplicates);Check("Ground spawn/repath uses first effective Up segment",_visual.Facing==EnemyFacing.Up);

            Check("Hysteresis keeps horizontal",EnemyDirectionalVisual.SelectFacing(new Vector2(1,1.1f),EnemyFacing.Right,true)==EnemyFacing.Right);

            Check("Hysteresis crosses dominant axis",EnemyDirectionalVisual.SelectFacing(new Vector2(1,1.3f),EnemyFacing.Right,true)==EnemyFacing.Up);

            Check("Hysteresis keeps vertical",EnemyDirectionalVisual.SelectFacing(new Vector2(1.1f,1),EnemyFacing.Up,true)==EnemyFacing.Up);

            var last=_visual.Facing;_visual.Face(Vector2.zero);Check("Zero displacement retains last direction",_visual.Facing==last);

            var artLeft=typeof(BaseEnemy).GetField("_artFaceLeft",BindingFlags.Instance|BindingFlags.NonPublic);

            artLeft.SetValue(_enemy,false);Route(Vector2.left);Check("ArtFaceLeft false left mirror",_enemy.transform.localScale.x<0);

            Route(Vector2.up);Check("Vertical clears old mirror",_enemy.transform.localScale.x>0);

            artLeft.SetValue(_enemy,true);

            var legacy=Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Prefabs/Enemy/Enemy_BugQueen.prefab")).GetComponent<BaseEnemy>();

            try

            {

                legacy.transform.position=Vector3.zero;

                var legacyConfig=new EnemyConfig(new cfg.EnemyData(990002,1,20,"Untouched legacy clone",0,1000,"Enemy_BugQueen",0,1,1,1,.3f,0,"","Review only",1));

                legacy.Init(legacyConfig,duplicates);float x=legacy.transform.localScale.x;

                // The legacy path advances one duplicate/near-zero waypoint per Tick.

                for(int tick=0;tick<4;tick++)legacy.Tick(.1f);

                Check("Untouched BugQueen has no directional component",!legacy.GetComponent<EnemyDirectionalVisual>());

                Check("Untouched legacy vertical movement and look-ahead mirror",x<0&&legacy.transform.localScale.x==x&&legacy.Position.y>0);

            }

            finally {Object.DestroyImmediate(legacy.gameObject);}

            _enemy.Init(Config(_request.name,_request.name=="Bat"),PathTo(_enemy.Position,_enemy.Position+Vector2.up*1000));

        }



        private static void EnterStage(int stage)

        {

            _stage=stage;_stageFrames=0;_scaledTime=0;_stageStart=EditorApplication.timeSinceStartup;_nextCapture=0;

            _positionStart=_enemy.Position;_phaseStart=_animator.GetCurrentAnimatorStateInfo(0).normalizedTime;

            if(stage<4){GameClock.Speed=1;_enemy.SetAnimState(EnemyAnimState.Walk);Route(Directions[stage]);}

            if(stage>=4&&stage<=7)_enemy.SetAnimState(new[]{EnemyAnimState.Idle,EnemyAnimState.Ready,EnemyAnimState.Walk,EnemyAnimState.Run}[stage-4]);

            if(stage==8){Route(Vector2.up);_enemy.SetAnimState(EnemyAnimState.Walk);_attackLeg=0;_attackLegStart=0;_angry=_returned=false;_enemy.TriggerAttackAnim();}

            if(stage==9)

            {

                float hp=_enemy.CurrentHp;_enemy.Hurt(2);

                Check("Real Hurt reduces HP",_enemy.CurrentHp==hp-2);

                Check("Hurt flashes every body renderer",_body.All(sr=>Flash(sr)>.99f));

                Check("HP fill shrinks and remains unmirrored",_enemy.transform.Find("HpBar/Fill").localScale.x<1&&_enemy.transform.Find("HpBar").lossyScale.x>0);

            }

            if(stage==10){if(_request.deathUp)Route(Vector2.up);_deadHead=_faded=_flashExpired=false;_enemy.Hurt(1000);}

            if(stage==11)

            {

                Check("Death automatically returned to EnemyManager pool",_enemy.IsFullyRecycled&&!_enemy.gameObject.activeSelf);

                var getPool=typeof(EnemyManager).GetMethod("GetPool",BindingFlags.Instance|BindingFlags.NonPublic);

                var pool=(ObjectPool<BaseEnemy>)getPool.Invoke(EnemyManager.Instance,new object[]{"Enemy_"+_request.name});

                if(pool.IdleCount==0)throw new InvalidOperationException("Automatic recycle did not produce a pooled instance.");

                var reused=pool.Get();Check("Actual manager pool returns the same instance",reused==_enemy);

                if(reused!=_enemy)throw new InvalidOperationException("Unexpected pooled instance.");

                _enemy.Init(Config(_request.name,_request.name=="Bat"),PathTo(_enemy.Position,_enemy.Position+Vector2.down*1000));

                Check("Reuse restores Down normal expression",_visual.Facing==EnemyFacing.Down&&_visual.HeadIndex==0&&_visual.Head.sprite==_visual.Profile.Down.NormalHead);

                Check("Reuse restores alpha, scale and white flash",_body.All(sr=>sr.color.a==1&&Flash(sr)==0)&&Mathf.Approximately(Mathf.Abs(_enemy.transform.localScale.x),_rootScale));

                Check("Reuse never restores ground shadow",NoShadow(_enemy));

            }

            if(stage==12){GameClock.Speed=1;GameClock.SetPaused(true);_pauseBaseline=false;}

            if(stage>=13&&stage<=15)

            {

                GameClock.SetPaused(false);GameClock.Speed=stage-12;Route(Vector2.up);_enemy.SetAnimState(EnemyAnimState.Walk);

                _positionStart=_enemy.Position;_phaseStart=_animator.GetCurrentAnimatorStateInfo(0).normalizedTime;

            }

            if(stage==16){GameClock.Speed=1;Route(Vector2.up);}

            if(stage==17){_enemy.OnRecycle();_enemy.Init(Config(_request.name,true),PathTo(_enemy.Position,_enemy.Position+Vector2.up*1000));_positionStart=_enemy.Position;}

        }



        private static void Update()

        {

            if(!Running||!EditorApplication.isPlaying||!_enemy||Time.frameCount==_lastFrame)return;

            try

            {

                if(BalancePlayModeVerifier.Running||GameClock.IsManualSimulation)throw new InvalidOperationException("Another verifier acquired the editor; stop this review.");

                _lastFrame=Time.frameCount;_stageFrames++;_scaledTime+=Time.deltaTime;

                float dt=GameClock.DeltaTime;

                _enemy.Tick(dt);

                double elapsed=EditorApplication.timeSinceStartup-_stageStart;

                if(elapsed>20)throw new TimeoutException("Stage exceeded real-frame timeout: "+StageNames[_stage]);

                Observe();

                if(elapsed>=_nextCapture){Capture(dt);_nextCapture=elapsed+.05;}

                bool advance=false;

                if(_stage<4&&_scaledTime>=1.1f)

                {

                    Check("Actual displacement "+StageNames[_stage],Vector2.Dot(_enemy.Position-_positionStart,Directions[_stage])>.9f);

                    Check("Direction "+StageNames[_stage],_visual.Facing==(EnemyFacing)new[]{2,3,0,1}[_stage]);

                    Check("One view visible "+StageNames[_stage],CorrectVisibility());

                    Check("No shadow "+StageNames[_stage],NoShadow(_enemy));

                    Check("HP world X positive "+StageNames[_stage],_enemy.transform.Find("HpBar").lossyScale.x>0);

                    float phase=_animator.GetCurrentAnimatorStateInfo(0).normalizedTime;int state=_animator.GetCurrentAnimatorStateInfo(0).fullPathHash;

                    Route(Directions[(_stage+1)%4]);

                    Check("Turn retains current state and exact phase "+_stage,_animator.GetCurrentAnimatorStateInfo(0).fullPathHash==state&&_animator.GetCurrentAnimatorStateInfo(0).normalizedTime==phase);

                    advance=true;

                }

                else if(_stage>=4&&_stage<=7&&_scaledTime>=.35f){Check("Actual state "+StageNames[_stage],_animator.GetCurrentAnimatorStateInfo(0).IsName(StageNames[_stage]));advance=true;}

                else if(_stage==8&&_scaledTime-_attackLegStart>=AttackDuration()+.5f)

                {

                    Check("Native attack event selects angry "+(_attackLeg==0?"Up":"Down")+" head",_angry);

                    Check("Native attack returns normal expression and Walk "+_attackLeg,_returned);

                    if(_attackLeg==0){_attackLeg=1;_attackLegStart=_scaledTime;Route(Vector2.down);_angry=_returned=false;_enemy.TriggerAttackAnim();}

                    else advance=true;

                }

                else if(_stage==9&&_scaledTime>=.18f){Check("Hurt white flash expires on every part",_body.All(sr=>Flash(sr)==0));advance=true;}

                else if(_stage==10&&_enemy.IsFullyRecycled){Check("Native death event selects directional dead head",_deadHead);Check("Death fades all body parts and shrinks",_faded);Check("Lethal flash expires before recycle",_flashExpired);advance=true;}

                else if(_stage==11&&_scaledTime>=.45f)advance=true;

                else if(_stage==12)

                {

                    if(_stageFrames==2){_pauseBaseline=true;_positionStart=_enemy.Position;_phaseStart=_animator.GetCurrentAnimatorStateInfo(0).normalizedTime;}

                    if(elapsed>=.6&&_stageFrames>=5){Check("Pause observed across actual Unity frames",_pauseBaseline&&_enemy.Position==_positionStart&&Mathf.Abs(_animator.GetCurrentAnimatorStateInfo(0).normalizedTime-_phaseStart)<.001f);advance=true;}

                }

                else if(_stage>=13&&_stage<=15&&_scaledTime>=.8f)

                {

                    float ratio=(_enemy.Position-_positionStart).magnitude/_scaledTime;

                    Check("Actual movement rate "+GameClock.Speed+"x",Mathf.Abs(ratio-GameClock.Speed)<.06f);

                    Check("Animator rate follows "+GameClock.Speed+"x",Mathf.Approximately(_animator.speed,GameClock.Speed)&&_animator.GetCurrentAnimatorStateInfo(0).normalizedTime>_phaseStart+.1f);

                    advance=true;

                }

                else if(_stage==16)

                {

                    int segment=Mathf.Min(3,(int)(_scaledTime/1.1f));Route(Directions[new[]{0,3,1,2}[segment]]);

                    if(_scaledTime>=4.4f){Check("Continuous turns remain shadowless",NoShadow(_enemy));advance=true;}

                }

                else if(_stage==17&&_scaledTime>=.7f){Check("Actual flying straight Up movement",_visual.Facing==EnemyFacing.Up&&_enemy.Position.y>_positionStart.y+.6f);advance=true;}

                if(advance){if(_stage==17)Finish();else EnterStage(_stage+1);}

            }

            catch(Exception error){Fail(error);}

        }



        private static bool CorrectVisibility()

        {

            bool vertical=_visual.Facing==EnemyFacing.Up||_visual.Facing==EnemyFacing.Down;

            if(!_visual.Profile.SeparateViewRigs)return Visible(_visual.Head)==vertical&&_visual.HorizontalRenderers.All(sr=>Visible(sr)==!vertical);

            bool up=_visual.Facing==EnemyFacing.Up;

            return _visual.HorizontalRenderers.All(sr=>sr.forceRenderingOff==vertical)

                &&_visual.UpRenderers.All(sr=>sr.forceRenderingOff==(!vertical||!up))

                &&_visual.DownRenderers.All(sr=>sr.forceRenderingOff==(!vertical||up));

        }



        private static void Observe()

        {

            if(_stage==8)

            {

                var parts=_attackLeg==0?_visual.Profile.Up:_visual.Profile.Down;

                _angry|=_animator.GetCurrentAnimatorStateInfo(0).IsName("Attack")&&_visual.HeadIndex==1&&_visual.Head.sprite==parts.AngryHead;

                _returned|=_angry&&_animator.GetCurrentAnimatorStateInfo(0).IsName("Walk")&&_visual.HeadIndex==0;

            }

            if(_stage==10&&!_enemy.IsFullyRecycled)

            {

                var deathParts=_request.deathUp?_visual.Profile.Up:_visual.Profile.Down;

                _deadHead|=_visual.HeadIndex==2&&_visual.Head.sprite==deathParts.DeadHead;

                _faded|=_body.All(sr=>sr.color.a<.95f)&&Mathf.Abs(_enemy.transform.localScale.x)<_rootScale*.99f;

                _flashExpired|=_scaledTime>.09f&&_body.All(sr=>Flash(sr)==0);

                CheckOnce("Death remains shadowless",NoShadow(_enemy));

            }

        }



        private static void CheckOnce(string name,bool pass)

        { if(!Checks.Any(c=>c.EndsWith(name,StringComparison.Ordinal)))Check(name,pass); }

        private static float AttackDuration()

        { return _animator.runtimeAnimatorController.animationClips.First(c=>c.name.StartsWith("Attack",StringComparison.Ordinal)).length; }



        private static void Capture(float dt)

        {

            // Camera belongs only to the unsaved review scene; project battlefield camera is untouched.

            // Fix framing for this character, preserving its original hover height and visible fade/shrink.

            _camera.transform.position=new Vector3(_enemy.Position.x+_cameraOffset.x,_enemy.Position.y+_cameraOffset.y,-10);

            _camera.orthographicSize=_cameraHalfSize;

            string file=StageNames[_stage]+"_"+(_captureIndex++).ToString("D05")+".png";

            _camera.Render();var previous=RenderTexture.active;

            try{RenderTexture.active=_target;_readback.ReadPixels(new Rect(0,0,768,768),0,0);_readback.Apply();File.WriteAllBytes(_out+"/frames/"+file,_readback.EncodeToPNG());}

            finally{RenderTexture.active=previous;}

            var state=_animator.GetCurrentAnimatorStateInfo(0);

            var observation=new Observation{stage=StageNames[_stage],state=StateName(state),facing=_visual.Facing.ToString(),file="frames/"+file,frame=Time.frameCount,expression=_visual.HeadIndex,realtime=EditorApplication.timeSinceStartup,

                unscaledDelta=Time.unscaledDeltaTime,simulationDelta=dt,speed=GameClock.Speed,normalizedTime=state.normalizedTime,hp=_enemy.CurrentHp,alpha=_visual.Head.color.a,flash=Flash(_visual.Head),position=_enemy.transform.position,scale=_enemy.transform.localScale,

                alive=_enemy.IsAlive,recycled=_enemy.IsFullyRecycled,paused=GameClock.IsPaused,headAngry=_visual.HeadIndex==1,shadow=!NoShadow(_enemy)};

            _frames.WriteLine(JsonUtility.ToJson(observation));_frames.Flush();

        }

        private static string StateName(AnimatorStateInfo info)

        { foreach(string name in new[]{"Idle","Ready","Walk","Run","Attack","Death"})if(info.IsName(name))return name;return info.fullPathHash.ToString(); }

        private static void Finish()

        {

            GameClock.SetPaused(false);GameClock.Speed=1;

            File.WriteAllText(_out+"/actual_runtime_checks.txt","Final installed assets; real Unity Play frames; no manual Animator.Update media. Unity "+Application.unityVersion+"\n"+string.Join("\n",Checks));

            Debug.Log("[EnemyDirectionBatchReview] "+_request.name+" checks="+Checks.Count+", failures="+Checks.Count(c=>c.StartsWith("FAIL",StringComparison.Ordinal))+"; "+_out);

            CloseFiles();EditorApplication.isPlaying=false;

        }

        private static void Fail(Exception error)

        {

            if(!string.IsNullOrEmpty(_out))File.WriteAllText(_out+"/exception.txt",error.ToString());

            Debug.LogException(error);GameClock.SetPaused(false);GameClock.Speed=1;CloseFiles();EditorApplication.isPlaying=false;

        }

        private static void CloseFiles()

        {

            if(_frames!=null){_frames.Dispose();_frames=null;}

            if(_camera)_camera.targetTexture=null;

            if(_target){_target.Release();Object.DestroyImmediate(_target);_target=null;}

            if(_readback){Object.DestroyImmediate(_readback);_readback=null;}

        }

    }

}

