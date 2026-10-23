<b>The shield raises the breathing-mode Q_m by 160–260×</b> at every mirror length (2, 4, 10 cells). The frequency does not move (9.813 GHz), so the shield does not perturb the cavity mode.

<b>Without the shield, Q_m saturates at ~1.5e7 beyond 4 mirror cells.</b> Adding mirror cells stops helping because the loss is the anchor slab, which radiates waves of every class (rings in the displacement map). Doubling the PML does not change it (1.65e7 both ways), so this is physical anchor loss, not a PML artifact.

<b>With the shield, Q_m is ~3e9 and limited by the shield itself.</b> Doubling the PML: 2.84e9 vs 2.83e9 (0.3 %). Finer slab mesh (22 vs 30 nm): 2.91e9 (+3 %). Two shield periods instead of four: 5.6e8 (5× lower), so the residual loss tunnels through the shield and more periods would raise Q_m further. The mirror length no longer matters beyond 4 cells (3.2e9 at 4, 2.8e9 at 10).

<b>Caveat.</b> Q_m above ~1e9 is an ideal-geometry, anchor-loss-only number. It passes the PML and mesh checks here, but real devices will be limited by disorder (which mixes symmetry classes), material and surface loss, and thermoelastic damping well before 1e9. Measured diamond OMCs reach ~3e4 (Joe 2026) to ~2e6 (Oh 2026). Read the result as: the shield removes anchor loss as the limiting mechanism.

<b>Fabrication note.</b> As modeled, the first shield column leaves a 30 nm strip of diamond at the trench edge (cross center a/2 = 225 nm from the edge, bar half-length 195 nm), below the 60 nm rule. The GDS (best_devices/) reproduces the model exactly. Fix before fabrication, with a re-run: move the lattice at least 30 nm away from the trench, or shorten the edge crosses.
