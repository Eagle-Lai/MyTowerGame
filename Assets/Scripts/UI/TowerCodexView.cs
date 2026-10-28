using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>Data-backed tower tabs and comparison, sharing reusable cards.</summary>
    public class TowerCodexView : MonoBehaviour
    {
        public const string LogicalName = "TowerCodexView";
        [SerializeField] private GameObject cardPrefab;
        private readonly List<TowerCodexItem> _cards = new List<TowerCodexItem>();
        private Transform _content;
        private TMP_Text _empty, _compareLabel, _title;
        private bool _comparison;
        private Button _retry;
        private int _requestVersion;
        private int _selectedIndex;
        private readonly Button[] _tabs=new Button[3];

        public void Configure(GameObject prefab) { cardPrefab = prefab; }

        private void Awake()
        {
            _content = transform.Find("Panel/Cards/Viewport/Content");
            _empty = transform.Find("Panel/Empty").GetComponent<TMP_Text>();
            _title = transform.Find("Panel/CodexTitle").GetComponent<TMP_Text>();
            _compareLabel = transform.Find("Panel/CompareBtn/Label").GetComponent<TMP_Text>();
            _retry = transform.Find("Panel/RetryBtn").GetComponent<Button>();
            _retry.onClick.AddListener(Retry);
            for(int i=0;i<_tabs.Length;i++)
            {
                int index=i;_tabs[i]=transform.Find("Panel/Tabs/Type"+i).GetComponent<Button>();
                _tabs[i].onClick.AddListener(()=>{_selectedIndex=index;_comparison=false;Refresh();});
            }
            transform.Find("Panel/CloseBtn").GetComponent<Button>().onClick.AddListener(Close);
            transform.Find("Panel/CompareBtn").GetComponent<Button>().onClick.AddListener(() =>
            {
                _comparison = !_comparison;
                Refresh();
            });
        }

        private void OnEnable()
        {
            EventDispatcher.AddEventListener<int>(EventName.LanguageChangedEvent, OnLanguageChanged);
            Refresh();
        }

        private void OnDisable()
        {
            _requestVersion++;
            EventDispatcher.RemoveEventListener<int>(EventName.LanguageChangedEvent, OnLanguageChanged);
        }

        private void OnLanguageChanged(int language) { Refresh(); }

        private void Retry()
        {
            int version = ++_requestVersion; _retry.interactable = false;
            _empty.text = Localization.Get("Loading config...") ?? "Loading config...";
            Configs.LoadAsync(ok =>
            {
                if (this == null || version != _requestVersion || !isActiveAndEnabled) return;
                _retry.interactable = true; Refresh();
            });
        }

        private void Refresh()
        {
            List<TowerConfig> towers = Configs.GetBaseTowers() ?? new List<TowerConfig>();
            _selectedIndex=Mathf.Clamp(_selectedIndex,0,Mathf.Max(0,towers.Count-1));
            while (_cards.Count < towers.Count)
            {
                GameObject card = Instantiate(cardPrefab, _content, false);
                UiAudio.Bind(card);
                card.SetActive(true);
                _cards.Add(card.GetComponent<TowerCodexItem>());
            }
            for (int i = 0; i < _cards.Count; i++)
            {
                _cards[i].gameObject.SetActive(i < towers.Count && (_comparison || i==_selectedIndex));
                if (i >= towers.Count) continue;
                _cards[i].SetData(towers[i], TowerCodexItem.RoleText(towers[i].Type));
                _cards[i].ShowComparison(_comparison);
            }
            for(int i=0;i<_tabs.Length;i++)
            {
                _tabs[i].gameObject.SetActive(!_comparison && i<towers.Count);
                if(i>=towers.Count)continue;
                var label=_tabs[i].GetComponentInChildren<TMP_Text>(true);label.text=towers[i].DisplayName;LanguageManager.ApplyFont(label);
                _tabs[i].GetComponent<Image>().color=i==_selectedIndex?new Color(.208f,.878f,1):new Color(.118f,.161f,.224f);
                label.color=i==_selectedIndex?new Color(.031f,.043f,.071f):new Color(.91f,.94f,.98f);
            }
            _title.text = Localization.Get("Tower Codex") ?? "Tower Codex";
            _compareLabel.text = Localization.Get(_comparison ? "Back" : "Compare") ?? (_comparison ? "Back" : "Compare");
            _empty.gameObject.SetActive(towers.Count == 0);
            _retry.gameObject.SetActive(towers.Count == 0); _retry.interactable = true;
            _empty.text = Localization.Get("Config load failed, see Console") ?? "Config load failed, see Console";
            LanguageManager.ApplyFont(_title);
            LanguageManager.ApplyFont(_compareLabel);
            LanguageManager.ApplyFont(_empty);
            GetComponent<TacticalForgeLayout>().SetTowerComparison(_comparison);
        }

        private void Close()
        {
            if(_comparison){_comparison=false;Refresh();return;}
            UIManager.Instance.Close(LogicalName);
            UIManager.Instance.Open<MainMenuView>(MainMenuView.LogicalName, UILayout.NormalPanel);
        }
    }
}
