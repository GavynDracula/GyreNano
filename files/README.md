# Print files / 打印文件

All dimensions are millimetres; use 100% scale. 3MF files contain geometry only, with no printer settings or G-code. No new slicing was performed for this release. Target trial printer: Creality K1C, 0.4 mm nozzle, PLA/PETG.

| Set | Purpose |
| --- | --- |
| [3x5](3x5/) | Earlier enclosure baseline for the existing Amoeba/Elite-C-holder build; right upper V11, left upper and bottoms V7 |
| [Integrated shells + FR4 retainers](integrated-fr4/README.md) | V14 upper shells with column/thumb mounts, V14 main retainers and V8 thumb retainers; current 0.6 mm FR4 route |
| [FPC direct supports](fpc-supports/README.md) | V31 print-oriented supports for bare V27 FPC; use with the integrated upper shells |
| [Fit trials](trials/) | Earlier holder/USB and ball/thumb samples |

Both integrated routes reuse the V7 bottom trays in `3x5/`. Do not print both FR4 and FPC retainers for the same build. Assembly motion, controller height, full cable routing, material durability and print tolerances are still awaiting physical trials.

中文：按实际使用 FR4 或 FPC 选择一套承托；整合外壳使用 integrated-fr4 中的左右上壳，底板继续用 3x5 中 V7。文件只是模型，用户自行切片。外壳与电路已做数字检查，尚未完成实际打印装配验证。
