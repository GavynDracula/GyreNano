# Geometry verification / 几何验证

Snapshot: right upper V11, left upper and both bottoms V7; checked 2026-11-10.
Measurements compare the exported meshes against the original meshes, not renders.

**The main-key, thumb-key and trackball-seat mounting relationships are preserved
within each half.** The table reports numerical comparison residuals, not manufacturing tolerances.

| Comparison | Maximum change |
| --- | --- |
| 35 switch aperture centres and sizes, in each key plane | 0 mm |
| Switch bearing-plane height | 1.74 × 10⁻¹⁵ mm |
| Switch-axis angle | 1.21 × 10⁻⁶ degrees |
| Pairwise key-centre vectors, including thumb to main keys | 1.47 × 10⁻¹⁴ mm |
| Thumb-centroid to main-key-centroid vector, both halves | 0 mm |
| Original ball-seat inner-wall samples (576 probes) | 0 mm |
| Fitted ball-seat centre, using the same probes on both meshes | 0 mm |
| Ball-seat normal, from 432 bearing-strip probes | 8.54 × 10⁻⁷ degrees |
| Ball-seat to any right-hand key vector | 1.43 × 10⁻¹⁴ mm |

These residuals are floating-point effects. Sources and raw measurements:
[relative layout](verification/relative-layout-verification.json),
[switch geometry](verification/key-geometry-verification.json),
[source attribution](ATTRIBUTION.md).

The ball datum is the **adapter seat**, not a directly measured physical sphere
centre. Using the same adapter and bearings retains their geometric relationship
to that seat; an assembled ball-centre measurement has not been performed.
The sampled bearing strip is at radii 23.05–23.14 mm. Outside it, the new enclosure
blends into the seat, so the surrounding surface is deliberately different.

The complete original mount core has no material removed above the check's
0.001 mm³ numerical tolerance. The specified adapter, BTU bottom and sensor cover
have no added static overlap above that tolerance. The top adapter retains about
0.276 mm³ overlap already present in the original reference pairing.
[Static assembly results](verification/trackball-assembly-checks-v11.json)

A continuous 35.2 mm capsule along the original inclined ball axis clears the
upper enclosure; the 34 mm sphere has a minimum radial margin of **0.649 mm**.
This checks ball insertion past the thumb region, not the adapter's installation
motion or contact inside the bearing assembly.
[Ball-clearance results](verification/ball34-clearance-v11.json)

Not covered by the preservation claim: new exterior surfaces, bottom-tray height
above the desk, the user-chosen spacing/rotation between halves, battery packaging,
complete adapter insertion, printing shrinkage or physical assembly fit.

## 中文结论

主键区、拇指键和原球座安装基准之间的相对位置与角度保持一致，数值差异仅为浮点误差。
这并不表示新外皮、过渡曲面或整机离桌高度与原版一样。球座基准不等于实际球心；沿用同一
adapter 和轴承时，其几何安装关系保留，但尚未实测装配后的球心位置。

34 mm 球经过拇指区的连续放入通道通过检查，径向余量约 0.649 mm；整个 adapter 的装入
动作仍待试装。当前适合作为开发版本留档，尚未完成实物定型。
