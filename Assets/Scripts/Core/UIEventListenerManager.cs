using UnityEngine;
using UnityEngine.EventSystems;
using System;
using System.Collections.Generic;

namespace FTProject
{
    public class UIEventListenerManager : MonoBehaviour
    {
        private enum Response
        {
            onClick = 1,
            onLongPress,
            endType,
        }

        public float clickTime
        {
            get { return time[(int)Response.onClick]; }
            set { time[(int)Response.onClick] = value; }
        }

        public float longTime
        {
            get { return time[(int)Response.onLongPress]; }
            set { time[(int)Response.onLongPress] = value; }
        }

        public static UIEventListenerManager _instance = null;
        public Util.VoidDelegate commonClickCallBack = null;

        public static UIEventListenerManager Instance()
        {
            if (_instance == null)
            {
                GameObject go = new GameObject("UIEventListenerManager");
                GameObject.DontDestroyOnLoad(go);
                _instance = go.AddComponent<UIEventListenerManager>();
                // _instance = new UIEventListenerManager();
            }
            return _instance;
        }

        public bool ClickResponse()
        {
            return CanResponse((int)Response.onClick);
        }

        public bool LongResponse()
        {
            return CanResponse((int)Response.onLongPress);
        }

        public void ClearCommonClickCallback()
        {
            commonClickCallBack = null;
        }

        private bool CanResponse(int _type)
        {
            double ts = GetTimeStamp();
            if (ts - _time[_type] > time[_type])
            {
                _time[_type] = ts;
                return true;
            }
            else
            {
                return false;
            }
        }

        private double GetTimeStamp(bool bflag = true)
        {
            TimeSpan ts = DateTime.UtcNow - _time1970;
            if (bflag)
                return ts.TotalSeconds;
            else
                return ts.TotalMilliseconds;
        }

        private DateTime _time1970 = new DateTime(1970, 1, 1, 0, 0, 0, 0);
        private double[] _time = new double[(int)Response.endType];
        private float[] time = new float[(int)Response.endType];

        private List<UIEventListener> longPressList = new List<UIEventListener>();

        public void AddLongPressObject(UIEventListener obj)
        {
            longPressList.Add(obj);
        }

        public void RemoveLongPressObject(UIEventListener obj)
        {
            longPressList.Remove(obj);
        }

        void Update()
        {
            if (longPressList.Count <= 0)
                return;

            for (int i = 0; i < longPressList.Count; i++)
            {
                longPressList[i].UpdatePointDown();
            }
        }
    }

    public class Util
    {
        public delegate void VoidDelegate(GameObject go, PointerEventData eventData = null);
        public delegate void VoidDelegateXArgs(params object[] args);

        public delegate void DragDelegate(PointerEventData eventData);
        public delegate void BoolDelagete(bool boolParam);

        //返回bool的无参代理
        public delegate bool BoolRetDelegate();
    }
    //public class UIEventListener : UnityEngine.EventSystems.EventTrigger{
    public class UIEventListener : MonoBehaviour, IPointerClickHandler, IBeginDragHandler, IEndDragHandler, IDragHandler, IPointerEnterHandler, IPointerExitHandler,
        IPointerDownHandler, IPointerUpHandler, ISubmitHandler
    {
        public string clickVoice = "Assets/Prefabs/Music/ui/ty/ui_ty001";
        private const float PRECISION = 0.000001f;

        public Util.VoidDelegate onClick;
        public Util.VoidDelegate onPointerDown;
        public Util.VoidDelegate onPointerUp;
        public Util.VoidDelegate onDragPointerEnter;
        public Util.VoidDelegate onDragPointerExit; 
        public Util.VoidDelegate onPointerEnter;
        public Util.VoidDelegate onPointerExit;
        public Util.VoidDelegate onLongPress;
        public Util.VoidDelegate onLongPressMoreThanOnce;
        public Util.DragDelegate onBeginDrag;
        public Util.DragDelegate onEndDrag;
        public Util.DragDelegate onDrag;
        public Util.VoidDelegate onSubmit;

        public bool isDisableClearTouch = false;
        public float doubleClickInterval = 0.3f;//两次点击间隔最短时间（秒计算）
        private bool isDrag = false;
        private bool isPointerDown = false;
        private bool isLongPressEnd = true;
        private bool isLongPressMoreThanOnceEnd = true;
        private float longPressTimer = 0f;
        private float longPressTime = 0.3f;
        private float longPressInterval = 0.3f;
        private float longPressMoreThanOnceTimer = 0f;
        private float longPressAcceleration = 0f;
        private float longPressMinInterval = 0.1f;
        private float longPressCurInterval = 0f;
        private double lastClickTime = 0;

        void PlayClickVoice()
        {
            if (clickVoice.Equals(""))
                return;
            //ioo.audioManager.Play2D(clickVoice);
        }

        public void UpdatePointDown()
        {
            //如果我在长安的期间，触发了，ondrag，那么longpress timer就重新计时
            if (!isPointerDown)
                return;

            longPressTimer += Time.deltaTime;
            longPressMoreThanOnceTimer += Time.deltaTime;
            if (!isLongPressEnd)
            {
                if (longPressTimer >= longPressTime)
                {
                    OnLongPress();
                    isLongPressEnd = true;
                    longPressTimer = 0f;
                }
            }
            if (!isLongPressMoreThanOnceEnd)
            {
                if (longPressMoreThanOnceTimer >= longPressCurInterval)
                {
                    OnLongPressMoreThanOnce();
                    longPressMoreThanOnceTimer = 0;
                    longPressCurInterval -= longPressAcceleration;
                    if (longPressCurInterval < longPressMinInterval)
                    {
                        longPressCurInterval = longPressMinInterval;
                    }
                }
            }
        }

        static public UIEventListener Get(GameObject go)
        {
            UIEventListener listener = go.GetComponent<UIEventListener>();
            if (listener == null) listener = go.AddComponent<UIEventListener>();
            return listener;
        }

        private double GetNowTime()
        {
            TimeSpan ts = DateTime.UtcNow - new DateTime(1970, 1, 1, 0, 0, 0, 0);
            return Convert.ToDouble(ts.TotalSeconds);
        }

        private bool CheckIsInTime()
        {
            if (Math.Abs(doubleClickInterval) <= PRECISION || Math.Abs(lastClickTime) <= PRECISION)
            {
                return true;
            }
            return GetNowTime() - lastClickTime >= doubleClickInterval;
        }

        private void UpdateNowClickTime()
        {
            if (Math.Abs(doubleClickInterval) <= PRECISION)
            {
                return;
            }
            lastClickTime = GetNowTime();
        }

        public void OnSubmit(BaseEventData eventData)
        {
            if (onSubmit != null)
                onSubmit(gameObject, eventData as PointerEventData);
        }

        public void OnPointerClick(PointerEventData eventData)
        {
            PlayClickVoice();

            if (UIEventListenerManager.Instance().commonClickCallBack != null)
            {
                UIEventListenerManager.Instance().commonClickCallBack(gameObject, eventData);
            }

            if (onClick != null && CheckIsInTime())
            {
                if (_hasClickResponse && !UIEventListenerManager.Instance().ClickResponse())
                {
                    return;
                }
                UpdateNowClickTime();
                //ioo.inputManager.MarkDealClickEvent();
                onClick(gameObject, eventData);
            }
        }

        public void OnPointerDown(PointerEventData eventData)
        {
            if (onPointerDown != null) onPointerDown(gameObject, eventData);
            UIEventListenerManager.Instance().AddLongPressObject(this);
            isPointerDown = true;
            isLongPressEnd = false;
            isLongPressMoreThanOnceEnd = false;
            longPressCurInterval = longPressInterval;
        }

        public void OnPointerUp(PointerEventData eventData)
        {
            if (onPointerUp != null) onPointerUp(gameObject, eventData);
            longPressTimer = 0f;
            longPressMoreThanOnceTimer = 0f;
            UIEventListenerManager.Instance().RemoveLongPressObject(this);
            isPointerDown = false;
            isLongPressEnd = true;
            isLongPressMoreThanOnceEnd = true;
        }

        void OnDisable()
        {
            // TODO,临时解决
            if (isDisableClearTouch)
            {
                longPressTimer = 0f;
                longPressMoreThanOnceTimer = 0f;
                UIEventListenerManager.Instance().RemoveLongPressObject(this);
                isPointerDown = false;
                isLongPressEnd = true;
                isLongPressMoreThanOnceEnd = true;
            }
        }

        public void OnPointerEnter(PointerEventData eventData)
        {
            if (onPointerEnter != null) onPointerEnter(gameObject, eventData);
            if (isDrag && (onDragPointerEnter != null)) onDragPointerEnter(gameObject, eventData);
        }

        public void OnPointerExit(PointerEventData eventData)
        {
            if (onPointerExit != null) onPointerExit(gameObject, eventData);
            if (isDrag && (onDragPointerExit != null)) onDragPointerExit(gameObject, eventData);
        }

        public void OnBeginDrag(PointerEventData eventData)
        {
            if (UIEventListenerManager.Instance().commonClickCallBack != null)
            {
                UIEventListenerManager.Instance().commonClickCallBack(gameObject, eventData);
            }
            isDrag = true;
            if (onBeginDrag != null) onBeginDrag(eventData);
        }

        public void OnEndDrag(PointerEventData eventData)
        {
            isDrag = false;
            if (onEndDrag != null) onEndDrag(eventData);
        }

        public void OnDrag(PointerEventData data)
        {
            if (onDrag != null) onDrag(data);
            UIEventListenerManager.Instance().RemoveLongPressObject(this);
            isPointerDown = false;
        }

        public void OnLongPress()
        {
            if (onLongPress != null) onLongPress(gameObject);
        }

        public void OnLongPressMoreThanOnce()
        {
            if (onLongPressMoreThanOnce != null) onLongPressMoreThanOnce(gameObject);
        }

        public float LongPressDuration
        {
            get { return longPressTime; }
            set { longPressTime = value; }
        }

        public float LongPressInterval
        {
            get
            {
                return longPressInterval;
            }
            set
            {
                longPressInterval = value;
            }
        }

        public float LongPressAcceleration
        {
            get
            {
                return longPressAcceleration;
            }
            set
            {
                longPressAcceleration = value;
            }
        }

        public float LongPressMinInterval
        {
            get
            {
                return longPressMinInterval;
            }
            set
            {
                longPressMinInterval = value;
            }
        }

        private Util.VoidDelegate _inputCallBack;

        private void InputEvent(string str)
        {
            if (_inputCallBack != null)
                _inputCallBack(gameObject);
        }

        public void AddValueChangeEventListener(Util.VoidDelegate Callback)
        {
            _inputCallBack = Callback;
            UnityEngine.UI.InputField inputField = gameObject.GetComponent<UnityEngine.UI.InputField>();
            if (inputField)
            {
                inputField.onValueChanged.AddListener(InputEvent);
            }
        }

        public void AddEndEditEventListener(Util.VoidDelegate Callback)
        {
            _inputCallBack = Callback;
            UnityEngine.UI.InputField inputField = gameObject.GetComponent<UnityEngine.UI.InputField>();
            if (inputField)
            {
                inputField.onEndEdit.AddListener(InputEvent);
            }
        }

        public void RemoveAllListenerForInputField()
        {
            UnityEngine.UI.InputField inputField = gameObject.GetComponent<UnityEngine.UI.InputField>();
            if (inputField)
            {
                inputField.onValueChanged.RemoveListener(InputEvent);
                inputField.onEndEdit.RemoveListener(InputEvent);
            }
            _inputCallBack = null;
        }

        private Util.VoidDelegateXArgs _scrollCallBack;
        private void ScrollEvent(Vector2 vec)
        {
            if (_scrollCallBack != null)
                _scrollCallBack(vec.x, vec.y);
        }

        public void AddScrollValueEvent(Util.VoidDelegateXArgs callback)
        {
            _scrollCallBack = callback;
            UnityEngine.UI.ScrollRect scrollRect = gameObject.GetComponent<UnityEngine.UI.ScrollRect>();
            if (scrollRect != null)
            {
                scrollRect.onValueChanged.AddListener(ScrollEvent);
            }
        }

        public void RemoveScrollValueEvent()
        {
            UnityEngine.UI.ScrollRect scrollRect = gameObject.GetComponent<UnityEngine.UI.ScrollRect>();
            if (scrollRect != null)
            {
                scrollRect.onValueChanged.RemoveListener(ScrollEvent);
            }
            _scrollCallBack = null;
        }

        public void EndLongPress()
        {
            longPressTimer = 0f;
            isLongPressEnd = true;
        }

        public void EndLongPressMoreThanOnce()
        {
            longPressMoreThanOnceTimer = 0f;
            isLongPressMoreThanOnceEnd = true;
        }

        public bool HasClickResponse
        {
            set
            {
                _hasClickResponse = value;
            }
            get
            {
                return _hasClickResponse;
            }
        }

        void OnDestroy()
        {
            onClick = null;
            onPointerDown = null;
            onPointerUp = null;
            onDragPointerEnter = null;
            onDragPointerExit = null;
            onPointerEnter = null;
            onPointerExit = null;
            onLongPress = null;
            onLongPressMoreThanOnce = null;
            onBeginDrag = null;
            onEndDrag = null;
            onDrag = null;
            _scrollCallBack = null;
            _inputCallBack = null;
            RemoveScrollValueEvent();
            RemoveAllListenerForInputField();
        }

        void Start()
        {
            UnityEngine.UI.Toggle tog = gameObject.GetComponent<UnityEngine.UI.Toggle>();
            _hasClickResponse = (tog == null);
        }

        private bool _hasClickResponse = true;
    }
}