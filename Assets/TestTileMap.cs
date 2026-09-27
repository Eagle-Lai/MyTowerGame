using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Tilemaps;
using UnityEditor;

namespace FTProject
{
    public class TestTileMap : MonoBehaviour
    {

        public Grid grid;
        public Tilemap tilemap;
        public int MaxNum;
        
        // Start is called before the first frame update
        public void Start()
        {
            int temp = MaxNum;
            if(tilemap == null)
            {
                tilemap = transform.GetComponent<Tilemap>();
            }
            BoundsInt boundsInt = tilemap.cellBounds;
            string result = "";
            for (int i = boundsInt.xMin; i < boundsInt.xMax; i++)
            {
                //Debug.Log(i);
                //if (i > 0)
                //{
                //    Debug.Log("$$$$$$$$$$$$$$$$$$$$$$$$$$");
                //    result += "\n";
                //}
                string tempstring = "";
                for (int j = boundsInt.yMin; j < boundsInt.yMax; j++)
                {
                    TileBase tileBase = tilemap.GetTile<TileBase>(new Vector3Int(i, j));
                    
                    if (tileBase != null)
                    {
                        switch (tileBase.name)
                        {
                            case "Start":
                                tempstring += "*";
                                break;
                            case "End":
                                tempstring += "&";
                                break;
                            case "Normal":
                                tempstring += "-";
                                break;
                            case "Obstacles":
                                tempstring += "#";
                                break;
                            case "Hide":
                                tempstring += "@";
                                break;
                            default:
                                break;
                        }
                        if(j == boundsInt.yMax - 1)
                        {
                            result += tempstring + "\n";
                        }
                    }
                }
            }
            
            Debug.Log(gameObject.name);
            //result = result.Replace("\r", "");
            Debug.Log(result);
            File.WriteAllText(Application.streamingAssetsPath + "/Map/" + gameObject.name + ".txt", result);
            //AssetDatabase.Refresh();
        }

        // Update is called once per frame
        void Update()
        {
            
        }
    }
}
