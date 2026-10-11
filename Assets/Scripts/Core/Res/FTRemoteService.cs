#if USE_YOOASSET
using System.Collections.Generic;
using YooAsset;

namespace FTProject
{
    /// <summary>
    /// YooAsset 远端服务实现：把 YooAsset 要的文件名翻译成真实下载 URL。
    ///
    /// ==================================================================
    /// 【YooAsset 什么时候会调它】
    ///   只在 **HostPlayMode（联机运行模式）** 下才会问远端地址：
    ///     · 请求包裹版本  → 要 `&lt;平台&gt;/&lt;包裹&gt;/&lt;版本&gt;/&lt;包裹&gt;.version`
    ///     · 加载包裹清单  → 要 `.../&lt;包裹&gt;_&lt;版本&gt;.bytes`（清单文件）
    ///     · 下载资源      → 要 `.../&lt;哈希&gt;.bundle`
    ///   离线 / 编辑器模拟模式下**根本不会走到这里**（那是本地文件系统的事）。
    ///
    /// 【为什么返回值是"列表"而不是单个字符串】
    ///   YooAsset 3.0.x 的接口设计成支持**多候选/多 CDN 备份**：
    ///   按优先级依次尝试，前一个失败会自动换下一个。本工程目前只配一个地址，
    ///   但保留了"主地址 + 备用地址"的扩展位，将来加 CDN 备份不用改接口。
    ///
    /// 【YooAsset 给的 fileName 长什么样】
    ///   **已经包含了相对路径**，形如 `Android/FreeTower/1.0.1/FreeTower.version`。
    ///   所以这里只需要做一个简单的"根地址 + / + 相对路径"拼接，
    ///   ★ 千万不要再自己拼平台名 —— 会变成 `.../Android/Android/...` 而 404。
    /// ==================================================================
    /// </summary>
    public class FTRemoteService : IRemoteService
    {
        /// <summary>服务器根地址（构造时固定下来，避免下载中途被改）</summary>
        private readonly string _root;

        public FTRemoteService(string root)
        {
            _root = string.IsNullOrEmpty(root) ? string.Empty : root.TrimEnd('/');
        }

        /// <summary>当前使用的根地址（诊断用）</summary>
        public string Root { get { return _root; } }

        public IReadOnlyList<string> GetRemoteUrls(string fileName)
        {
            var urls = new List<string>(2);

            if (string.IsNullOrEmpty(_root) || string.IsNullOrEmpty(fileName))
            {
                // 返回空列表 = 没有可用地址。YooAsset 会据此报"找不到远端地址"，
                // 这比返回一个错误 URL 更好定位问题（错误 URL 会报 404，看起来像服务器配错了）。
                return urls;
            }

            // 主地址：服务器根 + '/' + 相对路径
            // fileName 在 YooAsset 里用的是 '/' 分隔，不需要做平台相关的路径转换。
            string relative = fileName.TrimStart('/');
            urls.Add(_root + "/" + relative);

            return urls;
        }
    }
}
#endif
