using System;
using System.Collections.Generic;
using System.IO;
using FTProject;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;
using Object = UnityEngine.Object;

namespace FTProject.EditorTools
{
    // Anatomical-rig extension of EnemyDirectionPrefabBuilder. Never rebuilds a catalog.
    public static class EnemyDirectionalRigBuilder
    {
        private static readonly string[] Names = { "Bat", "BattlePanther", "Bear", "BearMounted", "BlackBear", "BlackBoar", "BlackWolf", "BlueScorpion", "Boar", "BoarMounted" };
        private static readonly string[] Families = { "Bats", "Felines", "Dogs", "Mounts", "Dogs", "Pigs", "Dogs", "Scorpions", "Pigs", "Mounts" };
        private static readonly string[] Controllers = { "Bat", "Feline", "Bear", "Bear", "Bear", "Boar", "Wolf", "Scorpion", "Boar", "Boar" };
        private const string FlashMaterial = "Assets/_UIAssets/Monsters/Birds/AdvancedHen/Directions/AdvancedHenFlash.mat";

        [Serializable] public sealed class Slice { public string name; public int x, y, w, h; public float pivotX = 0.5f, pivotY = 0.5f; }
        [Serializable] public sealed class Atlas { public int width, height, ppu; public Slice[] sprites; }
        [Serializable] public sealed class Part
        {
            public string name, sprite, role, alternate;
            public float x, y, width, height, angle;
            public int order, phase;
            public bool flipX;
        }
        [Serializable] public sealed class View { public string direction; public Part[] parts; }
        [Serializable] public sealed class Anatomy { public int legs, wings, claws, tails, arms, feelers; }
        [Serializable] public sealed class Layout { public Anatomy anatomy; public string motionKind; public int schema; public string name, controllerSource; public bool flying; public float referenceBottom, referenceHeight; public View[] views; }

        public static bool TryGetSpec(string name, out EnemyDirectionSpec spec)
        {
            for (int i = 0; i < Names.Length; i++)
            {
                if (Names[i] != name) continue;
                spec = new EnemyDirectionSpec
                {
                    Name = name, UseSeparateViewRigs = true,
                    ArtDir = "Assets/_UIAssets/Monsters/" + Families[i] + "/" + name + "/Directions",
                    PrefabPath = "Assets/Prefabs/Enemy/Enemy_" + name + ".prefab",
                    ControllerSource = "Assets/_UIAssets/Monsters/_Common/Animations/" + Controllers[i] + "/Controller.controller"
                };
                return true;
            }
            return EnemyDirectionRemainingCatalog.TryGetSpec(name, out spec);
        }

        [MenuItem("Tools/塔防/敌人方向批次/接入选中的单个战斗预制体")]
        public static void BuildSelected()
        {
            string path = AssetDatabase.GetAssetPath(Selection.activeObject);
            string name = Path.GetFileNameWithoutExtension(path);
            if (name.StartsWith("Enemy_", StringComparison.Ordinal)) name = name.Substring(6);
            EnemyDirectionSpec spec;
            if (!TryGetSpec(name, out spec) || path != spec.PrefabPath)
                throw new InvalidOperationException("请选择已授权批次中的单个战斗 prefab，未修改资源。");
            EnemyDirectionPrefabBuilder.Build(spec);
        }

        public static void Build(string name)
        {
            EnemyDirectionSpec spec;
            if (!TryGetSpec(name, out spec)) throw new InvalidOperationException("角色不在本批次授权范围：" + name);
            Build(spec);
        }

        public static bool Verify(EnemyDirectionSpec spec,out string report)
        {
            var lines=new List<string>();bool ok=true;
            Action<string,bool> check=(name,pass)=>{lines.Add((pass?"PASS ":"FAIL ")+name);ok&=pass;};
            var profile=AssetDatabase.LoadAssetAtPath<EnemyDirectionalProfile>(spec.ProfilePath);
            var prefab=AssetDatabase.LoadAssetAtPath<GameObject>(spec.PrefabPath);
            check("Complete installed profile",profile&&profile.IsComplete&&profile.SeparateViewRigs);
            check("Battle prefab imported",prefab);
            if(!profile||!prefab){report=string.Join("\n",lines);return false;}
            var dependencies=new HashSet<string>(AssetDatabase.GetDependencies(spec.PrefabPath,true));
            foreach(string dependency in new[]{spec.ProfilePath,spec.ArtDir+"/"+spec.Name+"_Directions.png",AssetDatabase.GetAssetPath(profile.Controller),FlashMaterial})
                check("Prefab dependency "+dependency,dependencies.Contains(dependency));
            var original=AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>(spec.ControllerSource);
            var copies=new Dictionary<string,AnimationClip>();
            foreach(var clip in profile.Controller.animationClips)if(clip)copies[clip.name]=clip;
            var seen=new HashSet<AnimationClip>();
            foreach(var source in original.animationClips)
            {
                if(!source||!seen.Add(source))continue;
                AnimationClip copy;
                if(!copies.TryGetValue(source.name+"_Directions",out copy)){check("Copied source clip "+source.name,false);continue;}
                bool curves=true;
                foreach(var binding in AnimationUtility.GetCurveBindings(source))
                {
                    var a=AnimationUtility.GetEditorCurve(source,binding);var b=AnimationUtility.GetEditorCurve(copy,binding);
                    if(b==null||a.length!=b.length){curves=false;break;}
                    for(int k=0;k<a.length;k++)
                    {
                        var x=a.keys[k];var y=b.keys[k];
                        curves&=x.time==y.time&&x.value==y.value&&x.inTangent==y.inTangent&&x.outTangent==y.outTangent&&x.inWeight==y.inWeight&&x.outWeight==y.outWeight&&x.weightedMode==y.weightedMode;
                    }
                }
                foreach(var binding in AnimationUtility.GetObjectReferenceCurveBindings(source))
                {
                    var a=AnimationUtility.GetObjectReferenceCurve(source,binding);var b=AnimationUtility.GetObjectReferenceCurve(copy,binding);
                    if(b==null||a.Length!=b.Length){curves=false;break;}
                    for(int k=0;k<a.Length;k++)curves&=a[k].time==b[k].time&&a[k].value==b[k].value;
                }
                check("Original horizontal curves retained "+source.name,curves);
                var events=AnimationUtility.GetAnimationEvents(copy);bool eventsRetained=true;
                foreach(var e in AnimationUtility.GetAnimationEvents(source))
                {
                    bool found=false;foreach(var c in events)found|=c.time==e.time&&c.functionName==e.functionName&&c.intParameter==e.intParameter&&c.stringParameter==e.stringParameter&&c.floatParameter==e.floatParameter&&c.objectReferenceParameter==e.objectReferenceParameter;
                    eventsRetained&=found;
                }
                check("Original events retained "+source.name,eventsRetained);
                var originalSettings=AnimationUtility.GetAnimationClipSettings(source);var copySettings=AnimationUtility.GetAnimationClipSettings(copy);
                check("Original clip duration/loop retained "+source.name,Mathf.Abs(source.length-copy.length)<.0001f&&originalSettings.loopTime==copySettings.loopTime);
            }
            var clone=PrefabUtility.LoadPrefabContents(spec.PrefabPath);
            try
            {
                var before=clone.transform.localToWorldMatrix;var hp=clone.transform.Find("HpBar");var hpBefore=hp.localToWorldMatrix;
                var receiver=clone.GetComponent<MonsterAnimEventReceiver>();var head=receiver.HeadRenderer;var heads=receiver.HeadSprites;
                for(int repeat=0;repeat<2;repeat++)
                {
                    bool applied=EnemyDirectionPrefabBuilder.ApplyIfConfigured(clone,string.IsNullOrEmpty(spec.OriginalAtlasPath)?spec.ArtDir.Substring(0,spec.ArtDir.Length-"/Directions".Length)+"/"+spec.Name+".png":spec.OriginalAtlasPath);
                    check("Rebuild hook applies on clone "+repeat,applied);
                    var nodes=clone.GetComponentsInChildren<Transform>(true);int shadows=0,groups=0;
                    foreach(var node in nodes){if(node.name=="Shadow")shadows++;if(node.name=="DirectionVisual")groups++;}
                    check("Repeat clone has one direction group/no Shadow "+repeat,shadows==0&&groups==1);
                    check("Repeat clone preserves root/HP/event receiver "+repeat,clone.transform.localToWorldMatrix==before&&hp.localToWorldMatrix==hpBefore&&receiver.HeadRenderer==head&&receiver.HeadSprites==heads);
                }
                foreach(var node in clone.GetComponentsInChildren<Transform>(true))check("No missing script "+node.name,GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(node.gameObject)==0);
            }
            finally{PrefabUtility.UnloadPrefabContents(clone);}
            // Existing collectors include both prefab and all direction dependencies; this does
            // not claim that a release bundle was built or read back.
            string collector=File.ReadAllText("Assets/BundleCollectorSetting.asset");
            check("YooAsset prefab and artwork collectors present",collector.Contains("CollectPath: Assets/Prefabs")&&collector.Contains("CollectPath: Assets/_UIAssets")&&collector.Contains("FilterRuleName: CollectAll"));
            report=string.Join("\n",lines);return ok;
        }

        public static Layout ReadLayout(EnemyDirectionSpec spec)
        {
            string path = spec.ArtDir + "/" + spec.Name + "_Directions.layout.json";
            if (!File.Exists(path)) throw new FileNotFoundException("缺少真实方向布局，未接入占位资源。", path);
            var layout = JsonUtility.FromJson<Layout>(File.ReadAllText(path));
            if (layout == null || layout.schema != 1 || layout.name != spec.Name || layout.views == null || layout.views.Length != 2)
                throw new InvalidOperationException("方向布局不完整：" + path);
            if (layout.controllerSource != spec.ControllerSource)
                throw new InvalidOperationException("原控制器引用与布局不一致：" + spec.Name);
            foreach (string direction in new[] { "Up", "Down" })
            {
                View view = FindView(layout, direction);
                if (view.parts == null || view.parts.Length < (layout.anatomy == null ? 3 : 2)) throw new InvalidOperationException(direction + " 缺少身体结构。");
                var names = new HashSet<string>(); bool head = false, body = false;int legs=0,wings=0,claws=0,tails=0,arms=0,feelers=0;
                foreach (Part part in view.parts)
                {
                    if (part == null || string.IsNullOrEmpty(part.name) || !names.Add(part.name) || string.IsNullOrEmpty(part.sprite)
                        || part.width <= 0 || part.height <= 0) throw new InvalidOperationException(direction + " 部件布局无效。");
                    head |= part.name == "Head"; body |= part.name == "Body";
                    if(part.role=="leg")legs++;if(part.role=="wing")wings++;if(part.role=="claw")claws++;if(part.role=="tail")tails++;if(part.role=="arm")arms++;if(part.role=="feeler")feelers++;
                    if(part.name.Contains("/")||float.IsNaN(part.x)||float.IsNaN(part.y)||float.IsInfinity(part.x)||float.IsInfinity(part.y))throw new InvalidOperationException("部件路径/坐标无效。");
                }
                if (!head || !body) throw new InvalidOperationException(direction + " 缺少头或躯干。");
                bool anatomy=spec.Name=="Bat"?wings==2&&legs==0&&claws==0&&tails==0:spec.Name=="BlueScorpion"?legs==6&&claws==2&&tails==1&&wings==0:legs==4&&tails==1&&wings==0&&claws==0;
                if(layout.anatomy != null) anatomy=legs==layout.anatomy.legs&&wings==layout.anatomy.wings&&claws==layout.anatomy.claws&&tails==layout.anatomy.tails&&arms==layout.anatomy.arms&&feelers==layout.anatomy.feelers;
                if(!anatomy)throw new InvalidOperationException(direction+" 的角色专属附肢结构不完整。");
            }
            return layout;
        }

        public static void Build(EnemyDirectionSpec spec)
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling)
                throw new InvalidOperationException("请在明确移交的非 Play、编译完成窗口接入。");
            Layout layout = ReadLayout(spec);
            string atlasPath = spec.ArtDir + "/" + spec.Name + "_Directions.png";
            string manifestPath = spec.ArtDir + "/" + spec.Name + "_Directions.sprites.json";
            if (!File.Exists(atlasPath) || !File.Exists(manifestPath)) throw new FileNotFoundException("方向图集或切片清单缺失，未修改 prefab。");
            var manifest = JsonUtility.FromJson<Atlas>(File.ReadAllText(manifestPath));
            ValidateManifest(manifest, layout);
            if (!AssetDatabase.LoadAssetAtPath<GameObject>(spec.PrefabPath) || !AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>(spec.ControllerSource)
                || !AssetDatabase.LoadAssetAtPath<Material>(FlashMaterial)) throw new InvalidOperationException("原 prefab/控制器/闪白材质依赖缺失。");
            var sprites = ImportAtlas(atlasPath, manifest);
            var profile = AssetDatabase.LoadAssetAtPath<EnemyDirectionalProfile>(spec.ProfilePath);
            if (!profile) { profile = ScriptableObject.CreateInstance<EnemyDirectionalProfile>(); AssetDatabase.CreateAsset(profile, spec.ProfilePath); }
            profile.SeparateViewRigs = true;
            profile.Up = ProfileParts(sprites, "Up"); profile.Down = ProfileParts(sprites, "Down");
            Directory.CreateDirectory(spec.AnimDir);
            AssetDatabase.ImportAsset(spec.AnimDir);
            profile.Controller = BuildController(spec, layout, sprites);
            EditorUtility.SetDirty(profile);
            GameObject root = PrefabUtility.LoadPrefabContents(spec.PrefabPath);
            try { Apply(root, profile, spec); PrefabUtility.SaveAsPrefabAsset(root, spec.PrefabPath); }
            finally { PrefabUtility.UnloadPrefabContents(root); }
            AssetDatabase.SaveAssets();
            Debug.Log("[EnemyDirection] 单例接入完成：" + spec.Name + "，真实正背分件；四向无地面阴影。");
        }

        private static View FindView(Layout layout, string direction)
        {
            foreach (View view in layout.views) if (view != null && view.direction == direction) return view;
            throw new InvalidOperationException("缺少方向：" + direction);
        }

        private static void ValidateManifest(Atlas atlas, Layout layout)
        {
            if (atlas == null || atlas.sprites == null || atlas.sprites.Length == 0 || atlas.ppu <= 0)
                throw new InvalidOperationException("切片清单为空。");
            var names = new HashSet<string>();
            foreach (Slice s in atlas.sprites)
                if (s == null || !names.Add(s.name) || s.w <= 0 || s.h <= 0 || s.x < 0 || s.y < 0 || s.x+s.w > atlas.width || s.y+s.h > atlas.height)
                    throw new InvalidOperationException("切片越界或重名。");
            foreach (View view in layout.views)
            {
                foreach (string expression in new[] { "HeadNormal", "HeadAngry", "HeadDead", "Body" })
                    if (!names.Contains(view.direction + "_" + expression)) throw new InvalidOperationException("缺少表情或躯干切片。");
                foreach (Part part in view.parts)
                    if (!names.Contains(part.sprite) || (!string.IsNullOrEmpty(part.alternate) && !names.Contains(part.alternate)))
                        throw new InvalidOperationException("部件切片缺失：" + part.name);
            }
        }

        private static Dictionary<string, Sprite> ImportAtlas(string path, Atlas manifest)
        {
            AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport);
            var importer = AssetImporter.GetAtPath(path) as TextureImporter;
            if (!importer) throw new InvalidOperationException("图集不是纹理。");
            importer.textureType = TextureImporterType.Sprite; importer.spriteImportMode = SpriteImportMode.Multiple;
            importer.spritePixelsPerUnit = manifest.ppu; importer.alphaIsTransparency = true;
            importer.mipmapEnabled = false; importer.filterMode = FilterMode.Bilinear; importer.wrapMode = TextureWrapMode.Clamp;
            importer.maxTextureSize = 2048; importer.textureCompression = TextureImporterCompression.Uncompressed;
            var settings = new TextureImporterSettings(); importer.ReadTextureSettings(settings);
            settings.spriteMeshType = SpriteMeshType.FullRect; importer.SetTextureSettings(settings);
            var metadata = new SpriteMetaData[manifest.sprites.Length];
            for (int i=0; i<metadata.Length; i++)
            {
                Slice s = manifest.sprites[i];
                metadata[i] = new SpriteMetaData { name=s.name, rect=new Rect(s.x,s.y,s.w,s.h), alignment=(int)SpriteAlignment.Custom, pivot=new Vector2(s.pivotX,s.pivotY) };
            }
            importer.spritesheet = metadata;
            foreach (string platform in new[] { "Android", "Standalone", "iPhone" })
            {
                var platformSettings = importer.GetPlatformTextureSettings(platform);
                platformSettings.overridden = false; importer.SetPlatformTextureSettings(platformSettings);
            }
            importer.SaveAndReimport();
            return LoadSprites(path);
        }

        private static Dictionary<string, Sprite> LoadSprites(string path)
        {
            var result = new Dictionary<string, Sprite>();
            foreach (Object obj in AssetDatabase.LoadAllAssetsAtPath(path)) { var sprite=obj as Sprite; if(sprite) result.Add(sprite.name,sprite); }
            return result;
        }

        private static EnemyDirectionalProfile.Parts ProfileParts(Dictionary<string, Sprite> sprites, string direction)
        {
            return new EnemyDirectionalProfile.Parts { NormalHead=sprites[direction+"_HeadNormal"], AngryHead=sprites[direction+"_HeadAngry"],
                DeadHead=sprites[direction+"_HeadDead"], Body=sprites[direction+"_Body"] };
        }

        public static void Apply(GameObject root, EnemyDirectionalProfile profile, EnemyDirectionSpec spec)
        {
            if (!profile || !profile.SeparateViewRigs || !profile.IsComplete) throw new InvalidOperationException("方向 Profile 不完整。");
            Layout layout = ReadLayout(spec);
            var sprites = LoadSprites(spec.ArtDir+"/"+spec.Name+"_Directions.png");
            var material = AssetDatabase.LoadAssetAtPath<Material>(FlashMaterial);
            if (!material) throw new InvalidOperationException("闪白材质丢失。");
            // Resolve every sprite before changing the clone.
            foreach(View view in layout.views) foreach(Part p in view.parts) if(!sprites.ContainsKey(p.sprite)) throw new InvalidOperationException("缺少部件："+p.sprite);
            Transform old = root.transform.Find("DirectionVisual"); if(old) Object.DestroyImmediate(old.gameObject);
            foreach(Transform node in root.GetComponentsInChildren<Transform>(true))
                if(node && node!=root.transform && node.name=="Shadow") Object.DestroyImmediate(node.gameObject);
            var horizontal = new List<SpriteRenderer>(); Transform hp=root.transform.Find("HpBar");
            foreach(SpriteRenderer sr in root.GetComponentsInChildren<SpriteRenderer>(true))
                if(!hp || !sr.transform.IsChildOf(hp)) { horizontal.Add(sr); sr.sharedMaterial=material; }
            var visual=root.GetComponent<EnemyDirectionalVisual>(); if(!visual) visual=root.AddComponent<EnemyDirectionalVisual>();
            visual.Profile=profile; visual.HorizontalRenderers=horizontal.ToArray();
            Transform group=new GameObject("DirectionVisual").transform; group.SetParent(root.transform,false);
            foreach(View view in layout.views)
            {
                Transform direction=new GameObject(view.direction).transform;direction.SetParent(group,false);
                Transform motion=new GameObject("Motion").transform;motion.SetParent(direction,false);
                float centerY=layout.referenceBottom+layout.referenceHeight*.5f;
                motion.localPosition=new Vector3(0,centerY,0);
                var renderers=new List<SpriteRenderer>(); SpriteRenderer head=null,body=null;
                foreach(Part part in view.parts)
                {
                    Transform pivot=new GameObject(part.name).transform;pivot.SetParent(motion,false);pivot.localPosition=new Vector3(part.x,part.y-centerY,0);pivot.localRotation=Quaternion.Euler(0,0,part.angle);
                    Transform leaf=new GameObject("Sprite").transform;leaf.SetParent(pivot,false);
                    Sprite sprite=sprites[part.sprite];float scale=Mathf.Min(part.width/sprite.bounds.size.x,part.height/sprite.bounds.size.y);
                    leaf.localScale=new Vector3(scale,scale,1);var sr=leaf.gameObject.AddComponent<SpriteRenderer>();
                    sr.sprite=sprite;sr.sharedMaterial=material;sr.sortingLayerName=BoardSorting.LayerMain;sr.sortingOrder=part.order;sr.flipX=part.flipX;
                    renderers.Add(sr);if(part.name=="Head")head=sr;if(part.name=="Body")body=sr;
                }
                if(view.direction=="Up") {visual.UpRenderers=renderers.ToArray();visual.UpHead=head;visual.UpBody=body;}
                else {visual.DownRenderers=renderers.ToArray();visual.DownHead=head;visual.DownBody=body;}
            }
            visual.Head=visual.DownHead;visual.Body=visual.DownBody;
            root.GetComponent<Animator>().runtimeAnimatorController=profile.Controller;
            visual.ResetForSpawn();
        }

        private static RuntimeAnimatorController BuildController(EnemyDirectionSpec spec, Layout layout, Dictionary<string, Sprite> sprites)
        {
            var source=AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>(spec.ControllerSource);
            var clips=new Dictionary<string,AnimationClip>();var seen=new HashSet<AnimationClip>();
            foreach(AnimationClip original in source.animationClips)
            {
                if(!original || !seen.Add(original))continue;
                AnimationClip copy=Object.Instantiate(original);copy.name=original.name+"_Directions";
                AddRigCurves(copy,original.name,layout,sprites);
                var events=new List<AnimationEvent>(AnimationUtility.GetAnimationEvents(copy));
                if(original.name=="Attack")
                {
                    bool angry=false,normal=false;foreach(var e in events)if(e.functionName=="SetHead"){angry|=e.intParameter==1;normal|=e.intParameter==0 && e.time>copy.length*.5f;}
                    if(!angry)events.Add(new AnimationEvent{functionName="SetHead",intParameter=1,time=copy.length*.18f});
                    if(!normal)events.Add(new AnimationEvent{functionName="SetHead",intParameter=0,time=copy.length*.96f});
                }
                if(original.name=="Death")
                {
                    bool dead=false;foreach(var e in events)dead|=e.functionName=="SetHead" && e.intParameter==2;
                    if(!dead)events.Add(new AnimationEvent{functionName="SetHead",intParameter=2,time=Mathf.Min(.03f,copy.length*.1f)});
                }
                events.Sort((a,b)=>a.time.CompareTo(b.time));AnimationUtility.SetAnimationEvents(copy,events.ToArray());
                string path=spec.AnimDir+"/"+original.name+"_Directions.anim";
                var installed=AssetDatabase.LoadAssetAtPath<AnimationClip>(path);
                if(installed){EditorUtility.CopySerialized(copy,installed);Object.DestroyImmediate(copy);}else{installed=copy;AssetDatabase.CreateAsset(installed,path);}
                clips[original.name]=installed;
            }
            foreach(string required in new[]{"Ready","Walk","Attack","Death"})if(!clips.ContainsKey(required))throw new InvalidOperationException("源动作缺少："+required);
            return EnemyDirectionPrefabBuilder.BuildAdvancedHenController(spec,clips);
        }

        private static void AddRigCurves(AnimationClip clip,string action,Layout layout,Dictionary<string,Sprite> sprites)
        {
            if (EnemyDirectionalAnimationPolish.TryAdd(clip, action, layout)) return;
            if (EnemyDirectionRemainingMotion.TryAdd(clip, action, layout, sprites)) return;
            float duration=Mathf.Max(.01f,clip.length);bool moving=action=="Walk",attack=action=="Attack",death=action=="Death";
            foreach(View view in layout.views)
            {
                string motion="DirectionVisual/"+view.direction+"/Motion";
                float centerY=layout.referenceBottom+layout.referenceHeight*.5f;
                Curve(clip,motion,"m_LocalPosition.x",duration,new[]{0f,0f});Curve(clip,motion,"m_LocalPosition.y",duration,new[]{centerY,centerY});Curve(clip,motion,"m_LocalPosition.z",duration,new[]{0f,0f});
                Curve(clip,motion,"localEulerAnglesRaw.z",duration,death?new[]{0f,-10f,-65f,-80f,-80f}:new[]{0f,0f});
                foreach(Part p in view.parts)
                {
                    string path=motion+"/"+p.name;float h=layout.referenceHeight;
                    float bob=p.role=="body"||p.role=="head"||p.role=="tail" ? h*(moving?.018f:.006f):0f;
                    float y=p.y-centerY;
                    float[] ys={y,y+bob,y,y+bob,y};
                    if(p.role=="leg" && moving){float lift=h*.045f;ys=p.phase==0?new[]{y,y+lift,y,y,y}:new[]{y,y,y,y+lift,y};}
                    Curve(clip,path,"m_LocalPosition.x",duration,new[]{p.x,p.x});Curve(clip,path,"m_LocalPosition.y",duration,ys);Curve(clip,path,"m_LocalPosition.z",duration,new[]{0f,0f});
                    float amplitude=p.role=="wing"?(death?8f:12f):p.role=="tail"?4f:p.role=="claw"?(attack?18f:3f):p.role=="head"&&attack?9f:p.role=="leg"&&moving?5f:0f;
                    float sign=p.flipX?-1:1;Curve(clip,path,"localEulerAnglesRaw.z",duration,new[]{p.angle,p.angle+amplitude*sign,p.angle,p.angle-amplitude*sign,p.angle});
                    if(p.role=="wing"&&!string.IsNullOrEmpty(p.alternate))
                    {
                        var binding=EditorCurveBinding.PPtrCurve(path+"/Sprite",typeof(SpriteRenderer),"m_Sprite");
                        var frames=new List<ObjectReferenceKeyframe>();
                        for(int frame=0;frame<4;frame++)frames.Add(new ObjectReferenceKeyframe{time=duration*frame/4f,value=sprites[!death && frame%2==1?p.alternate:p.sprite]});
                        AnimationUtility.SetObjectReferenceCurve(clip,binding,frames.ToArray());
                    }
                }
            }
            var settings=AnimationUtility.GetAnimationClipSettings(clip);settings.stopTime=duration;AnimationUtility.SetAnimationClipSettings(clip,settings);
        }

        private static void Curve(AnimationClip clip,string path,string property,float duration,float[] values)
        {
            var keys=new Keyframe[values.Length];for(int i=0;i<keys.Length;i++)keys[i]=new Keyframe(duration*i/(keys.Length-1),values[i]);
            var curve=new AnimationCurve(keys);for(int i=0;i<keys.Length;i++){AnimationUtility.SetKeyLeftTangentMode(curve,i,AnimationUtility.TangentMode.ClampedAuto);AnimationUtility.SetKeyRightTangentMode(curve,i,AnimationUtility.TangentMode.ClampedAuto);}
            AnimationUtility.SetEditorCurve(clip,EditorCurveBinding.FloatCurve(path,typeof(Transform),property),curve);
        }
    }
}
