# 制作来源与工具说明

音频内容：本包从原创音符事件、数学振荡器和确定性随机噪声生成。未使用第三方音频采样、真实录音、现成旋律、SoundFont 或卷积混响 IR。

制作代码与编曲：Source/synthesis.py、Source/produce.py；处理与测量：Source/finish.py。

工具：Python（PSF）、NumPy / SciPy（BSD 系列许可）、mido（MIT）、imageio-ffmpeg（BSD）、FFmpeg（实际构建配置见 Source/provenance.json，包含 libmp3lame 等）。这些是制作工具，不是声音素材。交付 ZIP 不包含工具二进制及安装缓存；工具本身的再分发须遵循各自上游许可。

本包中提供的脚本、音符事件、MIDI 和音频作为本次委托成果交付，可用于本游戏的编辑与后续制作。

固定种子与所有参数在源代码中；具体依赖版本见 Source/requirements.txt。精确波形请使用同样工具版本与渲染方式。
