using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

namespace FTProject
{
    public class PopMain : MonoBehaviour
    {
        /// <summary>
        /// 两个本地保存键。**不要写魔法字符串**：读写处各写一遍字面量，
        /// 一旦有一处拼错，症状是"存了但读不到"，而且不会有任何报错。
        /// </summary>
        private const string KeySlider = "Pop.SliderValue";
        private const string KeyText = "Pop.Content";

        public TextMeshProUGUI txt;
        public TMP_InputField input;
        public Button btn;
        public Button BgBtn;
        public Slider Slider;

        private float speed = 5000;

        private bool isShow;
        // Start is called before the first frame update
        void Start()
        {
            txt = transform.Find("Txt").GetComponent<TextMeshProUGUI>();
            btn = transform.Find("Send").GetComponent<Button>();
            Slider = transform.Find("Slider").GetComponent<Slider>();
            BgBtn = transform.Find("Button").GetComponent<Button>();
            input = transform.Find("InputField").GetComponent<TMP_InputField>();

            btn.onClick.AddListener(Send);
            BgBtn.onClick.AddListener(OnClickBgBtn);
            Slider.onValueChanged.AddListener(OnValueChange);
            isShow = true;
            Slider.value = LoadFloat(KeySlider, 0.5f);

            txt.text = LoadString(KeyText, "text");
        }

        // ---- 本地数据读写：统一走 SaveManager（SQLite/AES 持久化）----------
        // 【为什么不再用 PlayerPrefs】它是独立的存储系统，与游戏存档彼此隔离：
        //   清存档时清不掉它，换设备也带不走，而且明文可读。
        //   统一到 SaveManager 后，这类零散数据与关卡进度同库同事务，行为可预期。

        private static string LoadString(string key, string fallback)
        {
            string v;
            if (SaveManager.Instance.TryGetUserValue(key, out v) && !string.IsNullOrEmpty(v))
            {
                return v;
            }
            return fallback;
        }

        private static float LoadFloat(string key, float fallback)
        {
            string v;
            if (SaveManager.Instance.TryGetUserValue(key, out v) && !string.IsNullOrEmpty(v))
            {
                float f;
                if (float.TryParse(v, NumberStyles.Float, CultureInfo.InvariantCulture, out f))
                {
                    return f;
                }
            }
            return fallback;
        }

        private void OnValueChange(float value)
        {
            SaveManager.Instance.SetUserValue(
                KeySlider, value.ToString(CultureInfo.InvariantCulture), false);
        }

        private void Send()
        {
            txt.text = input.text;
            txt.transform.localPosition = new Vector3(1000, 0, 0);
            SaveManager.Instance.SetUserValue(KeyText, txt.text, false);
        }

        private void OnClickBgBtn()
        {
            isShow = !isShow;
            btn.gameObject.SetActive(isShow);
            input.gameObject.SetActive(isShow);
            Slider.gameObject.SetActive(isShow);
        }

        // Update is called once per frame
        void Update()
        {
            txt.transform.Translate(Vector3.left * speed * Time.deltaTime * Slider.value);
            float x = (txt.text.Length + 4) * 380;
            //Debug.Log(x);
            if (txt.transform.localPosition.x < -x)
            {
                txt.transform.localPosition = new Vector3(1000, 0, 0);
            }
        }
    }
}
