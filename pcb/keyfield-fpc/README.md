# FPC keyfield — V27

[简体中文](README.zh-CN.md)

One common 18-key artwork for both hands; use 18 keys on the left and omit/remove T_SW1/T_D1 for 17 on the right. **97.176 × 96.472 mm**, two-layer **0.11 mm PI FPC**, 1/3 oz copper. Existing holder pin maps and six keyfield FFCs per hand are retained.

[KiCad project](kicad/GyreNanoKeyfieldFPCV27.kicad_pro) · [submitted sample ZIP](fabrication/GyreNanoKeyfieldFPCV27-SampleED.zip) · [sample process notes](SAMPLE-FABRICATION.txt) · [BOM CSV](BOM.csv) · [采购清单](BOM.zh-CN.md)

The sample package requests adhesiveless electrodeposited copper, yellow coverlay, ENIG 1 µin and no factory stiffeners. It is a material/assembly experiment, not a production-qualified specification. The older quotation ZIP remains separately named for traceability.

JP1: bridge 1–2 for left, 2–3 for right; never both. Remove optional inter-region bridges for the screened installation. [DRC/ERC, 64 cut/hand cases, CAM and folded geometry evidence](checks/) is retained unchanged.

The original sample notes describe separately bonded FR4 backers. An alternative [printed direct-support set](../../models/fpc-supports/README.md) is now available; it replaces those backers in its modeled stack. Do not stack both support schemes without a fit review. FPC bending, soldering, hot-swap loads and complete cable/latch assembly remain to be tested.
