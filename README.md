<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg">
  <img alt="NANATATA — AI applications, interaction and engineering" src="assets/banner-light.svg">
</picture>

### 你好，我是 NANATATA 👋

**把想法，做成能用的东西。**

关注 AI 应用、人机交互与工程落地。目前在做两个 Windows 桌面软件：一个让 Live2D 形象陪着直播间聊天，一个把胶片放到电子观片台上细看和修图。两个都能下载到 exe，不是演示 demo。

**[个人网站上有这两个软件的网页演示，可以直接上手玩 →](https://yzh2006517.github.io/)**
给虚拟主播发条弹幕看它怎么接，或者拖着放大镜在胶卷上找细节。

[zhenhao897@gmail.com](mailto:zhenhao897@gmail.com)

---

## 作品

<a href="https://github.com/YZH2006517/ai-virtual-streamer">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/card-streamer-dark.svg">
    <img alt="AI 虚拟主播 — Live2D 数字人唠嗑直播软件" src="assets/card-streamer-light.svg">
  </picture>
</a>

### [AI 虚拟主播](https://github.com/YZH2006517/ai-virtual-streamer)

一个 Live2D 主播看着抖音弹幕陪观众聊天，还能跟着音乐跳舞、主持弹幕小游戏。下载一个 exe 就能用，填自己的大模型 API Key。

| 能做什么 | 实现重点 |
| --- | --- |
| 读弹幕回答 | 读直播间网页留言并排队，留言多时合并回答，支持屏蔽词 |
| 人设与形象 | 性格、声音、场景一键换；可导入自己的 Cubism 3 模型（zip） |
| 弹幕小游戏 | 猜数字、答题挑战由大模型现场出题，程序判题计分并上排行榜 |
| 舞台与导播 | 跟节拍跳舞，组件位置图层逐场景可调，WebView2 画面给 OBS 采集 |
| 成本可见 | 本地账本记录当天 token 花费与礼物收入 |

<sub>Python · Live2D Cubism · Edge TTS · WebView2 ｜ MIT ｜ API Key 用 Windows DPAPI 加密存本机</sub>

[网页演示](https://yzh2006517.github.io/#streamer) · [下载 Releases](https://github.com/YZH2006517/ai-virtual-streamer/releases) · [源码](https://github.com/YZH2006517/ai-virtual-streamer)

<br>

<a href="https://github.com/YZH2006517/Photo-All">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/card-photo-dark.svg">
    <img alt="Photo All Studio — 本地胶片电子观片台与修图工作台" src="assets/card-photo-light.svg">
  </picture>
</a>

### [Photo All Studio](https://github.com/YZH2006517/Photo-All)

一张可以开灯、摆片、放大细节的电子观片台，也是一套从选片到出片的本地工作台。原片只读，处理和识图都在本机完成。

| 能做什么 | 实现重点 |
| --- | --- |
| 电子观片台 | 实体灯箱式背光，自由拖片与一键平铺，连续胶卷首尾相接可横向滑动 |
| 折射放大镜 | 倍率与镜片尺寸独立调节，镜外保留整张台面 |
| 选片 | 颜色、冷暖、内容、风格等条件联动筛选，爱心选片与持久撤销 |
| 调色出片 | 曲线 / HSL / 质感，126 款开放 LUT，RAW 专业显影，16-bit 导出 |

<sub>Tauri · React · Python · RawTherapee · Spektrafilm · CLIP ONNX ｜ GPL-3.0 ｜ Windows 10/11 x64</sub>

[网页演示](https://yzh2006517.github.io/#photo) · [下载 Releases](https://github.com/YZH2006517/Photo-All/releases) · [源码](https://github.com/YZH2006517/Photo-All)

---

## 关注方向

- **AI 应用** — 让模型的理解与生成能力进入具体场景，而不是停在接口调用。
- **人机交互** — 把语言、语音、画面和实际操作连起来。
- **工程落地** — 完整链路、状态管理、异常处理，以及能交到别人手上的安装包。

## 联系

欢迎工作机会、科研交流与开源协作。

📮 **[zhenhao897@gmail.com](mailto:zhenhao897@gmail.com)** ｜ 🌐 **[yzh2006517.github.io](https://yzh2006517.github.io/)**
