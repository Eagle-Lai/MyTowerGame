using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using TMPro;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    public static class TacticalForgeAssets
    {
        public static void CreateFont()
        {
            const string folder=TacticalForgePrefabBuilder.Art+"/Fonts";
            AssetDatabase.Refresh();
            var source=AssetDatabase.LoadAssetAtPath<Font>(folder+"/NotoSansCJKsc-Regular.otf");
            if(source==null)throw new FileNotFoundException("Licensed Noto source font is missing.");
            var font=AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(folder+"/TacticalSans.asset");
            if(font==null)
            {
                font=TMP_FontAsset.CreateFontAsset(source,48,6,UnityEngine.TextCore.LowLevel.GlyphRenderMode.SDFAA,2048,2048,AtlasPopulationMode.Dynamic,true);
                font.name="TacticalSans";AssetDatabase.CreateAsset(font,folder+"/TacticalSans.asset");
                foreach(var atlas in font.atlasTextures){atlas.name="TacticalSans Atlas";AssetDatabase.AddObjectToAsset(atlas,font);}
                font.material.name="TacticalSans Material";AssetDatabase.AddObjectToAsset(font.material,font);
                // Warm only shipping localized characters. Further glyphs use the licensed dynamic source.
                string json=File.ReadAllText("Assets/ConfigJson/tblocalization.json");
                var rows=SimpleJSON.JSONNode.Parse(json);var chars=new HashSet<char>();
                foreach(SimpleJSON.JSONNode row in rows.Children)foreach(string language in new[]{"en","zhHans","zhHant"})foreach(char c in (string)row[language])chars.Add(c);
                foreach(char c in "0123456789★☆✓○−→/ .:%+-")chars.Add(c);
                string missing;font.TryAddCharacters(new string(chars.ToArray()),out missing);
                if(!string.IsNullOrEmpty(missing))Debug.LogWarning("[TacticalForge] Font missing characters: "+missing);
                EditorUtility.SetDirty(font);
            }
            var settings=AssetDatabase.LoadAssetAtPath<LocalizationSettings>("Assets/Localization/LocalizationSettings.asset");
            foreach(Language language in new[]{Language.English,Language.ChineseSimplified,Language.ChineseTraditional})
            {
                var entry=settings.fonts.Find(x=>x.language==language);
                if(entry==null)settings.fonts.Add(new LanguageFontEntry{language=language,font=font});else entry.font=font;
            }
            EditorUtility.SetDirty(settings);AssetDatabase.SaveAssets();
        }

        /// <summary>Copies an already-authored assembled direction frame. No enemy prefab is instantiated or imported.</summary>
        public static void CreatePortraits()
        {
            string folder=TacticalForgePrefabBuilder.Art+"/Portraits";Directory.CreateDirectory(folder);
            string revisionPath=folder+"/portrait-source-version.txt";
            bool rebuild=!File.Exists(revisionPath) || File.ReadAllText(revisionPath).Trim()!="sprite-composition-v2";
            var rows=SimpleJSON.JSONNode.Parse(File.ReadAllText("Assets/ConfigJson/tbenemydata.json"));
            var required=new HashSet<string>();foreach(SimpleJSON.JSONNode row in rows.Children)required.Add(row["resName"]);
            var portraits=new List<MonsterCodexPortrait>();var missing=new List<string>();
            foreach(string resource in required)
            {
                int index=Array.FindIndex(MonsterCatalog.Names,n=>"Enemy_"+n==resource);
                if(index<0){missing.Add(resource);continue;}
                string atlas=MonsterCatalog.AtlasPaths[index];string dir=System.IO.Path.GetDirectoryName(MonsterCatalog.SourcePaths[index]);
                string directions=dir+"/Directions/"+MonsterCatalog.Names[index]+"_Directions.png";
                string output=folder+"/"+resource+".png";
                if(rebuild || !File.Exists(output) || !HasVisiblePixels(output))
                {
                    // Direction sheets can contain separate heads/wings rather than complete frames.
                    // Copy the authored renderer hierarchy, never a single atlas body-part sprite.
                    if(!RenderSpritesOnly(MonsterCatalog.SourcePaths[index],output)){missing.Add(resource);continue;}
                    // Import into the existing asset path so its GUID and UI references survive repair.
                    AssetDatabase.ImportAsset(output, ImportAssetOptions.ForceUpdate);
                    var importer=(TextureImporter)AssetImporter.GetAtPath(output);importer.textureType=TextureImporterType.Sprite;importer.spriteImportMode=SpriteImportMode.Single;importer.alphaIsTransparency=true;importer.mipmapEnabled=false;importer.maxTextureSize=512;importer.SaveAndReimport();
                }
                portraits.Add(new MonsterCodexPortrait{resource=resource,sprite=AssetDatabase.LoadAssetAtPath<Sprite>(output)});
            }
            if(missing.Count==0)File.WriteAllText(revisionPath,"sprite-composition-v2\n");
            string path="Assets/Prefabs/UI/MonsterCodexView.prefab";var root=PrefabUtility.LoadPrefabContents(path);
            try{root.GetComponent<MonsterCodexView>().ConfigurePortraits(portraits);PrefabUtility.SaveAsPrefabAsset(root,path);}
            finally{PrefabUtility.UnloadPrefabContents(root);}
            path="Assets/Prefabs/UI/LevelDetailView.prefab";root=PrefabUtility.LoadPrefabContents(path);
            try{root.GetComponent<LevelDetailView>().ConfigureEnemyPortraits(AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Prefabs/UI/TacticalBriefingEnemyItem.prefab"),portraits);PrefabUtility.SaveAsPrefabAsset(root,path);}
            finally{PrefabUtility.UnloadPrefabContents(root);}
            Directory.CreateDirectory("Docs/UI_Redesign/Implementation/2026-10-26");
            File.WriteAllLines("Docs/UI_Redesign/Implementation/2026-10-26/missing-portraits.txt",missing);
            Debug.Log("[TacticalForge] Independent UI portraits: "+portraits.Count+"; unavailable assembled frames: "+missing.Count);
        }
        private static bool HasVisiblePixels(string path)
        {
            var image=new Texture2D(2,2,TextureFormat.RGBA32,false);
            try
            {
                if(!image.LoadImage(File.ReadAllBytes(path)))return false;
                foreach(var pixel in image.GetPixels32())if(pixel.a!=0)return true;
                return false;
            }
            finally{UnityEngine.Object.DestroyImmediate(image);}
        }
        private static bool RenderSpritesOnly(string sourcePath,string output)
        {
            GameObject source=AssetDatabase.LoadAssetAtPath<GameObject>(sourcePath);if(source==null)return false;
            // Read authored SpriteRenderers; create only transforms and renderers, never any enemy component.
            var scene=UnityEditor.SceneManagement.EditorSceneManager.NewPreviewScene();
            GameObject stage=new GameObject("Read-only sprite composition");
            UnityEngine.SceneManagement.SceneManager.MoveGameObjectToScene(stage,scene);
            RenderTexture previous=RenderTexture.active;var target=new RenderTexture(512,512,24);
            try
            {
                CopyVisual(source.transform,stage.transform);var renderers=stage.GetComponentsInChildren<SpriteRenderer>();
                if(renderers.Length==0)return false;Bounds bounds=renderers[0].bounds;foreach(var sr in renderers)bounds.Encapsulate(sr.bounds);
                var cameraObject=new GameObject("Portrait camera",typeof(Camera));cameraObject.transform.SetParent(stage.transform,false);
                var camera=cameraObject.GetComponent<Camera>();camera.scene=scene;camera.enabled=false;camera.cameraType=CameraType.Preview;camera.orthographic=true;camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=Color.clear;camera.cullingMask=1<<31;
                camera.nearClipPlane=.01f;camera.farClipPlane=100;camera.transform.position=new Vector3(bounds.center.x,bounds.center.y,bounds.center.z-20);
                camera.orthographicSize=Mathf.Max(bounds.size.x,bounds.size.y)*.56f;target.Create();camera.targetTexture=target;camera.Render();RenderTexture.active=target;
                var image=new Texture2D(512,512,TextureFormat.RGBA32,false);try{image.ReadPixels(new Rect(0,0,512,512),0,0);image.Apply();File.WriteAllBytes(output,image.EncodeToPNG());}finally{UnityEngine.Object.DestroyImmediate(image);}
                return true;
            }finally{RenderTexture.active=previous;target.Release();UnityEngine.Object.DestroyImmediate(target);UnityEditor.SceneManagement.EditorSceneManager.ClosePreviewScene(scene);}
        }
        private static void CopyVisual(Transform source,Transform parent)
        {
            if(!source.gameObject.activeSelf)return;var visual=new GameObject(source.name);visual.layer=31;visual.transform.SetParent(parent,false);
            visual.transform.localPosition=source.localPosition;visual.transform.localRotation=source.localRotation;visual.transform.localScale=source.localScale;
            var original=source.GetComponent<SpriteRenderer>();
            if(original!=null&&original.enabled&&original.sprite!=null)
            {
                var sr=visual.AddComponent<SpriteRenderer>();sr.sprite=original.sprite;sr.color=original.color;sr.flipX=original.flipX;sr.flipY=original.flipY;sr.sortingOrder=original.sortingOrder;
            }
            foreach(Transform child in source)CopyVisual(child,visual.transform);
        }
    }
}
