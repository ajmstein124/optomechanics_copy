// COMSOL GUI Method: test one k-point of Si mechanical band structure
//
// Instructions:
//   1. File > Open > C:\Users\JVadmin\Documents\optomechanics\unit_cell_3.mph
//   2. Developer tab > Methods > New Method
//   3. Paste this entire file, click Run (green arrow)
//
// Expected: solver runs (~1-2 min), prints 6 frequencies near 0-15 GHz.
// This validates: model loads, parameters set, solver runs, license works.

// Si nominal parameters
double a = 448e-9 * 1.067;   // 478 nm

model.param().set("a", String.valueOf(a));
model.param().set("d", "182e-9");
model.param().set("w", "99e-9");
model.param().set("f_r", "25e-9");
model.param().set("t", "220e-9");
model.param().set("N_mode", "6");
model.param().set("f_mech", "7e9");

// Gamma point
model.param().set("kFx", "0");
model.param().set("kFy", "0");

// Symmetric modes only
model.component("comp1").physics("solid").feature("as1").active(false);
model.component("comp1").physics("solid").feature("sym1").active(true);

System.out.println("Running solver...");
model.sol("sol1").runAll();
System.out.println("Done. Check Results > Datasets > dset1 for eigenfrequencies.");
System.out.println("If you see frequencies in the 0-15 GHz range, the pipeline works.");
