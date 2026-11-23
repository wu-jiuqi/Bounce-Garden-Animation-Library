# 喵弹拆箱 · 现用动画素材馆

**[在线打开动画素材馆](https://wu-jiuqi.github.io/Bounce-Garden-Animation-Library/)**

只收录当前 **0.4.0 / 45关** 游戏实际使用的序列帧：**62组动画、906帧、10类用途、39张原始PNG**。不再收录历史方案、废弃章节、美术试稿、旧标题和没有调用的元宝闪光。

支持搜索、按游戏用途筛选、名称与时长排序、调速、暂停、循环、逐帧检查、透明背景切换、轴心辅助线、序列图与单帧PNG下载。

## 收录标准

- 依据当前 Unity 播放代码、资源读取路径和切片元数据建立明确白名单，见 `runtime-policy.json`。
- 导出器只读取主工程现用资源，不扫描 `ArtSource`、历史构建、截图、录像或备份，也不收录重复的平台副本。
- 特殊砖只展示 `SevenSpecialFx` 使用的第7–15帧，9帧 / 0.66秒；招财猫只展示第3–15帧挥爪动作。已替换的待机图和静态蓄力状态不混入动画。
- 猫咪独立帧时长、强化球循环与碰撞帧段、结算光晕和云朵帧率均依当前代码导出。元宝特效采用默认施放时长，游戏中的激光时长可随场景变化。
- 网页展示序列原画；已应用相应游戏材质的透明度阈值，保留原画颜色；粒子、位移、旋转、渐隐、音效和补间不在网页叠加。切片的原始定位参数见 `metadata/`。五色特效按共享的 `sequence-layout.json` 读取不等距分隔；毛线、招财猫与发射猫保留实际轴心与身体缩放基准，详情可开启“显示轴心”。
- 原始PNG按SHA256保存，不改写像素；播放图集使用无损WebP。

## 本地打开

下载仓库后双击 `index.html` 即可查看。需要下载单帧PNG时，双击 Windows 下的 `serve.cmd`，或在本目录运行：

```sh
python -m http.server 8766 --bind 127.0.0.1
```

随后访问 http://localhost:8766 。网页不需要 Node.js 或构建步骤。

## 目录

| 路径 | 内容 |
| --- | --- |
| `index.html` / `style.css` / `app.js` | 动画展示页 |
| `catalog.json` / `catalog.js` | 当前动画清单、实际帧段、时长和来源 |
| `runtime-policy.json` | 经核对的现用资源白名单 |
| `assets/originals/` | 当前原始PNG，共39份 |
| `assets/previews/` | 无损序列图与首帧缩略图 |
| `metadata/` | 当前播放用到的7份切片元数据 |
| `verification/` | 完整性检查、清理与部署验证记录 |

## 更新与发布

```sh
python -m pip install -r requirements.txt
python scripts/collect.py --project "D:/Game/BounceBusters"
python scripts/test_slicing.py
python scripts/verify.py
node --check app.js
```

新增动画时先核对当前游戏调用，再更新导出规则和白名单。导出时自动删除未引用的图集、原图与元数据，校验器会拒绝历史来源和遗留文件。

提交 `main` 后发布：

```sh
python scripts/publish_pages.py
```

GitHub Pages 从 `gh-pages` 分支根目录发布，网址保持不变。素材仓库保留私有，线上展示公开可访问。

原画与项目资源的权利归原权利人所有，本仓库不授予额外的商用或再分发许可。

切片验证可由 Unity 的 `AnimationSliceParityBuild.Export` 导出实际Sprite参数，再运行 `python scripts/verify_unity_slices.py` 比对全部906帧。
