using System;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    [Serializable]
    public sealed class MonsterCodexPortrait
    {
        public string resource;
        public Sprite sprite;
    }
    /// <summary>Read-only catalogue; never instantiates a combat prefab or changes enemy assets.</summary>
    public sealed class MonsterCodexView : MonoBehaviour
    {
        public const string LogicalName = "MonsterCodexView";
        [SerializeField] private GameObject itemPrefab;
        [SerializeField] private List<MonsterCodexPortrait> portraits = new List<MonsterCodexPortrait>();
        private readonly List<GameObject> _items = new List<GameObject>();
        private readonly List<EnemyConfig> _enemies = new List<EnemyConfig>();
        private readonly Dictionary<string, List<EnemyConfig>> _variants = new Dictionary<string, List<EnemyConfig>>();
        private int _selected;
        private TMP_Text _name, _stats, _empty, _title;
        private Image _portrait;
        private Transform _content;
        private Button _retry;
        private int _requestVersion;
        private bool _detailOpen;
        public void Configure(GameObject item) { itemPrefab = item; }
        public void ConfigurePortraits(List<MonsterCodexPortrait> values) { portraits = values; }
        private void Awake()
        {
            _content=transform.Find("Panel/Grid/Viewport/Content");
            _name=transform.Find("Panel/Name").GetComponent<TMP_Text>();
            _stats=transform.Find("Panel/Stats").GetComponent<TMP_Text>();
            _empty=transform.Find("Panel/Empty").GetComponent<TMP_Text>();
            _title=transform.Find("Panel/Title").GetComponent<TMP_Text>();
            _portrait=transform.Find("Panel/Portrait").GetComponent<Image>();
            _retry=transform.Find("Panel/RetryBtn").GetComponent<Button>();
            _retry.onClick.AddListener(Retry);
            transform.Find("Panel/CloseBtn").GetComponent<Button>().onClick.AddListener(Close);
        }
        private void OnEnable() { EventDispatcher.AddEventListener<int>(EventName.LanguageChangedEvent,LanguageChanged);Build(); }
        private void OnDisable() {_requestVersion++;EventDispatcher.RemoveEventListener<int>(EventName.LanguageChangedEvent,LanguageChanged);}
        private void Retry()
        {
            int version=++_requestVersion;_retry.interactable=false;
            _empty.text=Localization.Get("Loading config...")??"Loading config...";
            Configs.LoadAsync(ok=>{if(this==null||version!=_requestVersion||!isActiveAndEnabled)return;_retry.interactable=true;Build();});
        }
        private void LanguageChanged(int language) { Build(); }
        private void Build()
        {
            _enemies.Clear();
            _variants.Clear();
            if(Configs.EnemyTable!=null) foreach(var raw in Configs.EnemyTable.DataList)
            {
                var enemy = new EnemyConfig(raw);
                if(!_variants.TryGetValue(enemy.ResName, out var variants))
                {
                    variants = new List<EnemyConfig>(); _variants.Add(enemy.ResName, variants); _enemies.Add(enemy);
                }
                variants.Add(enemy);
            }
            _enemies.Sort((a,b)=>a.Id.CompareTo(b.Id));
            _title.text=Localization.Get("Monster Codex") ?? "Monster Codex";LanguageManager.ApplyFont(_title);
            bool empty=_enemies.Count==0;_empty.gameObject.SetActive(empty);_portrait.gameObject.SetActive(!empty);
            _content.parent.parent.gameObject.SetActive(!empty && !_detailOpen);
            _retry.gameObject.SetActive(empty);_retry.interactable=true;
            _empty.text=Localization.Get("Config load failed, see Console")??"Config load failed, see Console";
            LanguageManager.ApplyFont(_empty);
            if(empty){_name.text=_stats.text=string.Empty;_name.gameObject.SetActive(false);_stats.gameObject.SetActive(false);return;}
            if(itemPrefab==null)throw new InvalidOperationException("Monster codex item prefab is unassigned.");
            while(_items.Count<_enemies.Count)
            {
                int index=_items.Count;var item=Instantiate(itemPrefab,_content,false);UiAudio.Bind(item);
                item.transform.Find("Body").GetComponent<Button>().onClick.AddListener(()=>Select(index));_items.Add(item);
            }
            for(int i=0;i<_items.Count;i++)
            {
                _items[i].SetActive(i<_enemies.Count);if(i>=_enemies.Count)continue;
                var label=_items[i].transform.Find("Body/Label").GetComponent<TMP_Text>();
                label.text=Localization.Get(_enemies[i].Name)??_enemies[i].Name;LanguageManager.ApplyFont(label);
                var detail=_items[i].transform.Find("Body/Details/Label").GetComponent<TMP_Text>();detail.text=Localization.Get("View Details")??"View Details";LanguageManager.ApplyFont(detail);
                var icon=_items[i].transform.Find("Body/Portrait").GetComponent<Image>();
                var portrait=portraits.Find(x=>x.resource==_enemies[i].ResName);
                icon.sprite=portrait!=null?portrait.sprite:null;icon.enabled=icon.sprite!=null;
            }
            Select(Mathf.Clamp(_selected,0,_enemies.Count-1),false);
        }
        private void Select(int index,bool openDetail=true)
        {
            if(openDetail)_detailOpen=true;
            _selected=index;EnemyConfig enemy=_enemies[index];
            for(int i=0;i<_items.Count;i++)_items[i].transform.Find("Body").GetComponent<Outline>().effectColor=i==index?new Color(.208f,.878f,1):new Color(.325f,.404f,.498f);
            _name.text=Localization.Get(enemy.Name)??enemy.Name;
            List<EnemyConfig> variants=_variants[enemy.ResName];
            _stats.text=string.Format("{0}\nHP  {1}\n{2}  {3}\n{4}  {5}\n{6}  {7}\n\n{8}",
                Localization.Get("Configured variants: {0}",variants.Count)??("Configured variants: "+variants.Count),
                Range(variants,x=>x.Hp,"0.#"),Localization.Get("Speed")??"Speed",Range(variants,x=>x.Speed,"0.##"),
                Localization.Get("Armor")??"Armor",Range(variants,x=>x.Armor,"P0"),
                Localization.Get("Gold")??"Gold",Range(variants,x=>x.Reward,"0"),Localization.Get(enemy.Desc)??enemy.Desc);
            MonsterCodexPortrait portrait=portraits.Find(x=>x.resource==enemy.ResName);
            _portrait.sprite=portrait!=null?portrait.sprite:null;_portrait.enabled=_portrait.sprite!=null;
            if(!_portrait.enabled)_stats.text+="\n"+(Localization.Get("Unavailable")??"Unavailable");
            LanguageManager.ApplyFont(_name);LanguageManager.ApplyFont(_stats);
            ApplyMode();
        }
        private static string Range(List<EnemyConfig> values,Func<EnemyConfig,float> read,string format)
        {
            float min=float.MaxValue,max=float.MinValue;
            foreach(var value in values){float n=read(value);min=Mathf.Min(min,n);max=Mathf.Max(max,n);}
            return Mathf.Approximately(min,max)?min.ToString(format):min.ToString(format)+" – "+max.ToString(format);
        }
        private void ApplyMode()
        {
            bool available=_enemies.Count>0;
            _content.parent.parent.gameObject.SetActive(available && !_detailOpen);
            _name.gameObject.SetActive(available && _detailOpen);_stats.gameObject.SetActive(available && _detailOpen);_portrait.gameObject.SetActive(available && _detailOpen);
            GetComponent<TacticalForgeLayout>().Refresh();
        }
        private void Close()
        {
            if(_detailOpen){_detailOpen=false;ApplyMode();return;}
            UIManager.Instance.Close(LogicalName);UIManager.Instance.Open<MainMenuView>(MainMenuView.LogicalName,UILayout.NormalPanel);
        }
    }
}
