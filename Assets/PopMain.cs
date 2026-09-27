using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

namespace FTProject
{
    public class PopMain : MonoBehaviour
    {
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
            Slider.value = PlayerPrefs.GetFloat("PopValue", 0.5f);
            
            txt.text = PlayerPrefs.GetString("Pop", "text");
        }

        private void OnValueChange(float value)
        {
            PlayerPrefs.SetFloat("PopValue", value);
        }

        private void Send()
        {
            txt.text = input.text;
            txt.transform.localPosition = new Vector3(1000, 0, 0);
            PlayerPrefs.SetString("Pop", txt.text);
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
