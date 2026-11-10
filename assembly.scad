// Millimetres. Development assembly; see README.md before printing.
// Each STL is in its own print datum. Tray shifts down 7.3 mm in assembly.
part = "assembly"; // assembly, left, right, left_tray, right_tray
tray_depth = 7.3;
show_trackball = false; // supplied original components, in assembly coordinates
module shell(side) { import(str("exports/",side,"-closed-development.stl")); }
module tray(side) { import(str("exports/",side,"-bottom-development.stl")); }
module half(side) {
    color([.55,.70,.76]) shell(side);
    color([.23,.29,.33]) translate([0,0,-tray_depth]) tray(side);
    if(side=="right" && show_trackball) {
        color([.8,.42,.12]) import("references/trackball-top-assembly-v7.stl");
        color([.23,.58,.24]) import("references/trackball-btu-assembly-v7.stl");
        color([.48,.23,.58]) import("references/trackball-cover-assembly-v7.stl");
    }
}
if(part=="assembly") {
    translate([-150,0,0]) half("left");
    translate([150,0,0]) half("right");
} else if(part=="left" || part=="right") shell(part);
else if(part=="left_tray") tray("left");
else if(part=="right_tray") tray("right");
