using System.Text;

namespace FTProject
{
    /// <summary>评分展示的共用文案与格式，不参与评分计算。</summary>
    public static class RatingPresentation
    {
        public static string ProfileName(string profileId)
        {
            string key;
            switch (profileId)
            {
                case "D01": key = "Very Easy"; break;
                case "D02": key = "Easy"; break;
                case "D03": key = "Below Medium"; break;
                case "D04": key = "Medium"; break;
                case "D05": key = "Above Medium"; break;
                case "D06": key = "Hard"; break;
                case "D07": key = "Very Hard"; break;
                case "D08": key = "Extreme"; break;
                default: return string.IsNullOrEmpty(profileId) ? "—" : profileId;
            }
            return Localization.Get(key) ?? key;
        }

        public static string Time(long milliseconds)
        {
            if (milliseconds <= 0) return "--:--.---";
            return string.Format("{0:00}:{1:00}.{2:000}", milliseconds / 60000,
                milliseconds / 1000 % 60, milliseconds % 1000);
        }

        public static string Reasons(LevelRatingResult result)
        {
            if (result == null) return Localization.Get("Rating config missing or invalid") ?? "评分配置缺失或无效";
            if (result.reasons == null || result.reasons.Length == 0)
                return Localization.Get("All five-star conditions met") ?? "已满足全部五星条件";
            StringBuilder text = new StringBuilder();
            for (int i = 0; i < result.reasons.Length; i++)
            {
                string reason = result.reasons[i];
                if (string.IsNullOrEmpty(reason)) continue;
                if (text.Length > 0) text.Append(" · ");
                text.Append(Localization.Get(reason) ?? reason);
            }
            return text.ToString();
        }
    }
}
