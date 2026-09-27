using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using FTProject;
                 
public class MapGenerator : MonoBehaviour
{
    // Start is called before the first frame update
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        
    }
    [MenuItem("GameObject/生成地图", priority = -1)]
    public static void Test()
    {
        GameObject go = Selection.activeObject as GameObject;
        Debug.LogError(go.name);
        GameObject map = GameObject.Instantiate(go);
        map.name = map.name.Replace("(Clone)", "");
        TestTileMap MapComponent = map.GetComponent<TestTileMap>();
        if(MapComponent == null)
        {
            MapComponent = go.AddComponent<TestTileMap>();
        }
        MapComponent.Start();
        GameObject.DestroyImmediate(map);
        AssetDatabase.Refresh();
    }
}
