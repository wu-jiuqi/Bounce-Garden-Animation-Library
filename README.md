# 喵弹拆箱 · 序列帧动画素材馆

## 在线展示

**[点击打开动画素材馆](https://wu-jiuqi.github.io/Bounce-Garden-Animation-Library/)**

直接在浏览器查看、播放和逐帧检查动画，无需下载仓库或安装依赖。

Bounce Garden / BounceBusters 项目的独立动画资源归档与展示界面。

本次归档：**167 组独立序列、2,806 帧、41 个素材系列**；其中63组为主工程运行资源。保留1,655份原始PNG文件，整理后约451MB。

## 本地浏览

克隆或下载整个仓库，双击 `index.html` 即可浏览和播放。页面为原生 HTML / CSS / JavaScript，无需 Node.js、安装依赖或构建。

如需下载单帧 PNG，请双击 Windows 下的 `serve.cmd`，再访问 http://localhost:8766 。也可以在本目录运行：

```sh
python -m http.server 8766 --bind 127.0.0.1
```

支持素材系列与版本筛选、名称/源文件搜索、播放/暂停、0.25×～2×调速、循环切换、时间轴、上一帧/下一帧、逐帧缩略图、三种预览背景、透明序列图与原始 PNG 下载。播放面板支持空格播放/暂停及左右方向键逐帧。

## 目录

| 路径 | 内容 |
| --- | --- |
| `index.html` / `style.css` / `app.js` | 自适应动画展示页 |
| `catalog.json` | 机器可读清单，含源路径、SHA256、尺寸、帧序、逐帧时长和重复来源 |
| `catalog.js` | 与 JSON 相同的数据，允许离线打开页面 |
| `assets/originals/` | 内容哈希命名的原始 PNG，字节保持不变 |
| `assets/previews/` | 统一画布的无损 WebP 序列图与缩略图 |
| `metadata/` | 原项目美术清单与切片布局 |
| `scripts/collect.py` | 从原工程重新盘点与导出 |
| `scripts/verify.py` | 素材完整性、帧时长与原图哈希校验 |
| `verification/` | 本次验证记录 |

## 收录范围与解释

- 从主工程 `BounceGarden/BounceGarden/Assets/Resources/Art` 的代码切图资源及 `ArtSource` 中的导出帧、动画元数据整理。
- 当前运行资源与历史素材分别标记。“运行资源”表示资源与主工程读取规则对应，不表示每个动画都会在当前45关出现。
- Android、微信等镜像工程相同资源不重复收录；历史文件序列按画面内容去重，同时保留其他来源。缓存、备份、构建产物、游戏录像、截图以及静态 UI/图标不作为独立动画。
- 已知猫咪逐帧时长、果冻消除帧率、毛线脱层时长等保留原始参数。保留历史原稿中用于跳过某帧的 0ms 时长。没有可靠时间参数时明确标为 **预览帧率**，使用 12fps。
- 部分旧图集同时包含静止状态与动作阶段，按原始编号完整展示，便于检查素材。特定动作可拖动时间轴检查。
- 网页展示序列原画，不模拟 Unity Shader、粒子、位移、旋转、音效和补间。五色特殊砖展示其16帧阶段映射，游戏前7帧使用的方砖静态贴图不在此叠加。
- 预览图保持 RGBA，按共同画布居中排版；原始切片/轴心/定位参数以 `metadata` 为准。WebP 图集按从左至右、从上至下读取，列数见清单。
- 原画及项目资源的权利归原权利人所有，本仓库不授予额外的商用或再分发许可。

## 更新素材

需要 Python 3 与 Pillow：

```sh
python -m pip install -r requirements.txt
python scripts/collect.py --project "D:/Game/BounceBusters"
python scripts/verify.py
node --check app.js
```

导出脚本只读原工程，输出到本仓库。新增代码切图格式时，在脚本中登记切片规则；不要通过图集长宽猜测静态图标是否为动画。

本仓库保持私有，在线动画素材馆通过 GitHub Pages 公开访问。`gh-pages` 发布分支只包含展示页、动画清单和素材，不包含维护脚本与项目元数据。

更新素材后，先提交 `main`，再运行以下命令更新同一个在线地址：

```sh
python scripts/verify.py
python scripts/publish_pages.py
```

GitHub Pages 使用 `gh-pages` 分支根目录发布。部署状态可在仓库的 Actions / Pages 设置中查看。
