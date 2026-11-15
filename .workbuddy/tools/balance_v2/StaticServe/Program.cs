// 本地静态预览：只读地提供 Docs/BalanceV2 下的文件
var root = Path.GetFullPath(args.Length > 0 ? args[0] : ".");
var port = args.Length > 1 ? args[1] : "8765";
var app = WebApplication.Create();
app.UseDefaultFiles(new DefaultFilesOptions { FileProvider = new Microsoft.Extensions.FileProviders.PhysicalFileProvider(root), DefaultFileNames = { "05_难度曲线.html" } });
app.UseStaticFiles(new StaticFileOptions { FileProvider = new Microsoft.Extensions.FileProviders.PhysicalFileProvider(root), ServeUnknownFileTypes = true });
app.Run($"http://localhost:{port}");
