# Print files / 打印文件

All dimensions are millimetres; use 100% scale. 3MF files contain geometry only, with no printer settings or G-code. No new slicing was performed for this release. Target trial printer: Creality K1C, 0.4 mm nozzle, PLA/PETG.

| Set | Purpose |
| --- | --- |
| [3x5](3x5/) | Earlier enclosure baseline for the existing Amoeba/Elite-C-holder build; right upper V11, left upper and bottoms V7 |
| [Current integrated-shoulder shells](raised-rim/README.md) | MK2-inspired raised shoulders and rounded forward ball collar; retain existing key/ball datums, bottoms and FR4/FPC supports; geometry checked, physical trial pending |
| [V14 reference shells + FR4 retainers](integrated-fr4/README.md) | Earlier upper shells, matching V14 main retainers and V8 thumb retainers for the current 0.6 mm FR4 route |
| [FPC direct supports](fpc-supports/README.md) | V31 print-oriented supports for bare V27 FPC; use with the integrated upper shells |
| [Fit trials](trials/) | Earlier holder/USB and ball/thumb samples |

Both integrated routes reuse the V7 bottom trays in `3x5/`. Do not print both FR4 and FPC retainers for the same build. Assembly motion, controller height, full cable routing, material durability and print tolerances are still awaiting physical trials.

中文：当前上壳使用 raised-rim 中的左右模型，按实际使用 FR4 或 FPC 选择一套承托；底板继续用 3x5 中 V7。文件只是模型，用户自行切片。外壳与电路已做数字检查，尚未完成实际打印装配验证。

当前 [raised-rim](raised-rim/README.md) 已整合加高肩部、外缘接缝修整和球仓外沿收圆；保留早期上壳以便比较。

Repository naming: `models/` replaces `files/`. Already-published v0.2.0-prototype.1 archives and the historical engineering snapshot retain their original `files/` paths and checksums.

目录名称已改为 `models/`；已发布压缩包保留原 `files/` 路径，模型内容相同。
