// Cupwarmer v1 enclosure prototype.
// Units: millimeters.
//
// This is a mechanical study model, not a production CAD source.
// It captures the current enclosure intent:
// - no cup-contact metal
// - direct flat thermal pad on the flexible heater for the first thermal trial
// - integrated low centering rim, kept away from the pad cup-contact face
// - heater cable drops internally to the PCB
// - non-metal Qi-facing bottom shell

/* [View] */

// Show a vertical cutaway through the model.
show_cutaway = false;

// Separate the upper stack for inspection.
show_exploded = false;

// Distance between exploded stack layers.
explode_gap = 7.0;

// Master toggle for non-enclosure reference parts.
show_reference_stack = true;

/* [Visibility] */

show_cup_contact_pad = true;
show_aluminum_spreader = false;
show_flexible_heater = true;
show_insulation = true;
show_pcb_reference = true;
show_ferrite_reference = true;
show_rx_coil_reference = true;
show_bottom_tray = true;

/* [Quality] */

$fn = 128;

// Main envelope.
enclosure_od = 60.0;
wall = 1.6;
bottom_floor_th = 1.0;
spreader_pocket_od = 55.2;
spreader_pocket_depth = 0.45;

// Integrated centering rim. It is part of the bottom tray and surrounds the
// TP-4 without covering it. The rim is intentionally just a low side wall:
// every stack layer can drop in from the top, and the pad remains replaceable.
rim_od = enclosure_od;              // flush with the enclosure outer wall
rim_h = 0.50;                       // rises from pad bottom; well below pad top
pad_to_rim_radial_gap = 0.00;       // nominal side contact for centering

// Functional round parts.
// pcb/ferrite/insulation shrink to 50 mm so they pass the heater-seat bore
// opening and drop to the floor; only the heater/spreader/pad stay ~56 mm.
use_aluminum_spreader = false;
pcb_od = 50.0;
pcb_th = 1.0;
// Heater stays larger than the 50 mm stack so it lands on the seat step, but
// trimmed to 55 mm so it clears the centering rim for top-loading.
heater_od = 55.0;
heater_th = 0.35;
pad_od = 55.0;                      // cut TP-4 to sit inside the rim, not under it
pad_th = 1.00;
pad_crown_h = 0.00;                 // ARCTIC TP-4 samples are treated as flat sheets
spreader_od = 54.5;
spreader_th = 0.30;
rim_inner_od = pad_od + 2 * pad_to_rim_radial_gap;
lip_top_below_pad = pad_th - rim_h;

// Qi reference stack.
// L1: Wuerth Elektronik 760308102207, WE-WPCC Qi RX coil.
// Datasheet size: 40x40x1.2 mm rounded square, visible corner radius about 5-8 mm.
coil_x = 40.0;
coil_y = 40.0;
coil_corner_r = 6.0;
coil_th = 1.20;
ferrite_od = 50.0;
ferrite_th = 0.50;
insulation_od = 50.0;
insulation_th = 0.70;
f1_clearance_gap = 1.4;

// Assembly clearances.
radial_clearance = 0.35;
tray_inner_od = enclosure_od - 2 * wall;
pcb_clear_od = pcb_od + 2 * radial_clearance;
coil_corner_max_r = sqrt(2) * (coil_x / 2 - coil_corner_r) + coil_corner_r;
coil_clear_od = 2 * (coil_corner_max_r + radial_clearance);
lower_stack_bore_od = max(pcb_clear_od, ferrite_od + 2 * radial_clearance, coil_clear_od);
upper_stack_bore_od = rim_inner_od; // straight side wall: no inward ledge/lip
coil_pocket_clearance = 0.35;
coil_pocket_x = coil_x + 2 * coil_pocket_clearance;
coil_pocket_y = coil_y + 2 * coil_pocket_clearance;
coil_pocket_corner_r = coil_corner_r + coil_pocket_clearance;
lower_stack_support_od = lower_stack_bore_od;

// Z positions in assembled view.
z_bottom_floor_top = bottom_floor_th;
z_coil = z_bottom_floor_top + 0.20;
z_ferrite = z_coil + coil_th + 0.20;
lower_stack_support_z = z_bottom_floor_top;
lower_stack_support_h = z_ferrite - lower_stack_support_z;
z_pcb = z_ferrite + ferrite_th + 0.35;
z_insulation = z_pcb + pcb_th + 0.25;
z_heater = z_insulation + insulation_th + f1_clearance_gap;
z_spreader = z_heater + heater_th;
z_pad = z_spreader + (use_aluminum_spreader ? spreader_th : 0);
z_rim = z_pad;
rim_top_z = z_rim + rim_h;
tray_body_h = z_rim;
bottom_tray_h = rim_top_z;
z_lip_pocket_bottom = z_spreader - spreader_pocket_depth;

// Overall external height: tray floor bottom (z=0) to cup contact pad top.
overall_height = z_pad + pad_th;
echo(str("overall height (tray bottom -> pad top) = ", overall_height, " mm"));
echo(str("integrated centering rim below pad top = ", lip_top_below_pad, " mm"));
echo(str("pad-to-rim nominal radial gap = ", pad_to_rim_radial_gap, " mm"));
echo(str("lower stack bore OD = ", lower_stack_bore_od, " mm"));
echo(str("coil pocket keepout = ", coil_pocket_x, " x ", coil_pocket_y, " mm"));

// Heater cable drops internally from the heater underside to PCB pads.
// Heater J1 pads in hardware/kicad/heater/heater.kicad_pcb are centered at
// (100, 122.5), i.e. (0, +22.5) relative to the 56 mm heater board center.
heater_cable_x = 0.0;
heater_cable_y = 22.5;
heater_cable_w = 24.0;
heater_cable_d = 5.0;
heater_cable_drop_h = z_heater - (z_pcb + pcb_th);
heater_cable_slot_clearance = 0.40;

// F1: Xucheng Elec KSD9700-70/5JSB/080C, LCSC C156512 (current part).
// Leaded bimetal thermostat in a phi 8.9 x 28 mm metal can + 80 mm tinned leads.
// Reverted from SMD NR72CB0 (C183007) / SA77SB0 (C143808) because the JLCPCB
// flexible-heater process requires laser welding for those; KSD9700-70 is
// wire-solderable. JLCPCB heater service includes F1 in the heater assembly,
// bonded to the heater hotspot in series with H+.
// WARNING: the f1_* dims below are STALE SMD placeholders (4.8 x 3.2 x 0.89 mm)
// and the 1.4 mm f1_clearance_gap no longer fits the can. Rework the stack to
// the can geometry (pocket / relocate F1 off-center) before trusting this model.
f1_x = 4.8;  // STALE placeholder; real part is a phi 8.9 x 28 mm can
f1_y = 3.2;  // STALE placeholder
f1_z = 0.89; // STALE placeholder; can lying flat is ~8.9 mm tall
f1_corner_r = 0.35;
f1_on_heater_x = 0;
f1_on_heater_y = -14.0;
f1_on_heater_z = -f1_z;

// PCB support. H1/H2 are KiCad mounting holes on the 50 mm PCB, expressed
// relative to the board/enclosure center at (100,100) in cupwarmer-hw.kicad_pcb.
// Keep these centers and pcb_mounting_hole_d in sync with the PCB footprint.
// The screw bosses are disabled for the direct-pad enclosure study because a
// 40x40 mm centered L1 coil overlaps both boss locations. Keep the PCB holes
// visible, but do not print bosses in the bottom tray unless the coil/holes are
// moved in a later PCB/mechanical revision.
use_pcb_screw_bosses = false;
pcb_support_holes = [
  [21.0, -8.0], // H1 = (121, 92)
  [-21.0, 8.0]  // H2 = (79, 108)
];
pcb_support_rib_count = len(pcb_support_holes);
pcb_mounting_hole_d = 2.4;
pcb_support_rib_w = 5.0;
pcb_support_rib_depth = 2.4;
pcb_support_outer_r = pcb_clear_od / 2;
pcb_support_inner_r = pcb_support_outer_r - pcb_support_rib_depth;
pcb_support_z = bottom_floor_th;
pcb_support_h = z_pcb - bottom_floor_th;
// Cylindrical boss on each rib for an M2 plastic self-tap screw through the
// matching PCB clearance hole.
pcb_support_boss_d = pcb_support_rib_w;
pcb_support_pilot_d = 1.7;
pcb_support_pilot_depth = 4.0;

// Taller stack retention ribs. These collide with the centered 40x40 mm coil
// unless the coil/ferrite are notched, so they are disabled in the v1 direct-pad
// enclosure model. Keep the geometry for later revisions if perimeter datum
// ribs are still useful after the coil support strategy is settled.
use_stack_retention_ribs = false;
stack_retention_rib_count = 4;
stack_retention_rib_angle0 = 30;
stack_retention_rib_w = 4.0;
stack_retention_outer_r = enclosure_od / 2 - wall;
stack_retention_rib_depth = stack_retention_outer_r - (spreader_pocket_od / 2 - 0.2 - 2.0);
stack_retention_inner_r = stack_retention_outer_r - stack_retention_rib_depth;
stack_retention_rib_h = z_lip_pocket_bottom - bottom_floor_th;
stack_retention_slot_clearance = 0.35;

module cyl(d, h) {
  cylinder(d = d, h = h);
}

module annulus(od, id, h) {
  difference() {
    cyl(od, h);
    translate([0, 0, -0.05]) cyl(id, h + 0.10);
  }
}

module rounded_rect_2d(x, y, r) {
  hull() {
    translate([x / 2 - r, y / 2 - r]) circle(r = r);
    translate([-x / 2 + r, y / 2 - r]) circle(r = r);
    translate([x / 2 - r, -y / 2 + r]) circle(r = r);
    translate([-x / 2 + r, -y / 2 + r]) circle(r = r);
  }
}

module rounded_box(x, y, r, h) {
  linear_extrude(height = h)
    rounded_rect_2d(x, y, r);
}

module lower_stack_support_shelf() {
  // Broad left/right shelves in the margin between the round tray bore and the
  // rounded-rect RX coil keepout. The top/bottom sides stay open for coil
  // leadout and assembly clearance.
  side_shelf_w = (lower_stack_support_od - coil_pocket_x) / 2;
  translate([0, 0, lower_stack_support_z])
    intersection() {
      cyl(lower_stack_support_od, lower_stack_support_h);
      union() {
        translate([coil_pocket_x / 2, -lower_stack_support_od / 2, 0])
          cube([side_shelf_w, lower_stack_support_od, lower_stack_support_h]);
        translate([-lower_stack_support_od / 2, -lower_stack_support_od / 2, 0])
          cube([side_shelf_w, lower_stack_support_od, lower_stack_support_h]);
      }
    }
}

module maybe_cutaway() {
  if (show_cutaway) {
    difference() {
      children();
      translate([-enclosure_od, -enclosure_od, -5])
        cube([enclosure_od, 2 * enclosure_od, 30]);
    }
  } else {
    children();
  }
}

module stack_retention_ribs() {
  for (i = [0 : stack_retention_rib_count - 1]) {
    rotate([0, 0, i * 360 / stack_retention_rib_count + stack_retention_rib_angle0])
      translate([stack_retention_inner_r, -stack_retention_rib_w / 2, bottom_floor_th])
        cube([stack_retention_rib_depth, stack_retention_rib_w, stack_retention_rib_h]);
  }
}

module pcb_support_ribs() {
  for (i = [0 : pcb_support_rib_count - 1]) {
    support_xy = pcb_support_holes[i];
    support_angle = atan2(support_xy[1], support_xy[0]);
    rotate([0, 0, support_angle]) {
      difference() {
        hull() {
          translate([pcb_support_inner_r, -pcb_support_rib_w / 2, pcb_support_z])
            cube([pcb_support_rib_depth, pcb_support_rib_w, pcb_support_h]);
          translate([norm(support_xy), 0, pcb_support_z])
            cyl(pcb_support_boss_d, pcb_support_h);
        }
        translate([norm(support_xy), 0,
                   pcb_support_z + pcb_support_h - pcb_support_pilot_depth])
          cyl(pcb_support_pilot_d, pcb_support_pilot_depth + 0.10);
      }
    }
  }
}

module pcb_mounting_hole_cutouts(h) {
  for (support_xy = pcb_support_holes) {
    translate([support_xy[0], support_xy[1], -0.05])
      cyl(pcb_mounting_hole_d, h + 0.10);
  }
}

module heater_cable_insulation_slot(h) {
  translate([
    heater_cable_x - heater_cable_w / 2 - heater_cable_slot_clearance,
    heater_cable_y - heater_cable_d / 2 - heater_cable_slot_clearance,
    -0.05
  ])
    cube([
      heater_cable_w + 2 * heater_cable_slot_clearance,
      heater_cable_d + 2 * heater_cable_slot_clearance,
      h + 0.10
    ]);
}

module stack_retention_edge_slots(h) {
  slot_inner_r = stack_retention_inner_r - stack_retention_slot_clearance;
  slot_depth = stack_retention_rib_depth + 2 * stack_retention_slot_clearance;
  slot_w = stack_retention_rib_w + 2 * stack_retention_slot_clearance;

  for (i = [0 : stack_retention_rib_count - 1]) {
    rotate([0, 0, i * 360 / stack_retention_rib_count + stack_retention_rib_angle0])
      translate([slot_inner_r, -slot_w / 2, -0.05])
        cube([slot_depth, slot_w, h + 0.10]);
  }
}

module bottom_tray() {
  color([0.18, 0.18, 0.18, 1.0])
    maybe_cutaway()
      union() {
        difference() {
          cyl(enclosure_od, tray_body_h);

          // Stepped bore. Lower bore clears the 50 mm PCB/ferrite stack and the
          // rounded 40x40 mm coil corners down to the floor. The upper bore
          // opens to the centering-rim inner diameter and runs straight from
          // the heater seat to the rim base. The step face at
          // z_heater is the heater seat: the heater lands on it while the 50 mm
          // parts drop through the lower bore. The floor stays solid for Qi.
          // Pad lateral location is by the low integrated rim above this body;
          // the pad is not tucked under or overlapped by the rim.
          translate([0, 0, bottom_floor_th])
            cyl(lower_stack_bore_od, z_heater - bottom_floor_th);
          translate([0, 0, z_heater])
            cyl(upper_stack_bore_od, tray_body_h - z_heater + 0.20);
        }

        // Integrated centering rim, printed as one piece with the tray.
        translate([0, 0, z_rim])
          annulus(rim_od, rim_inner_od, rim_h);

        lower_stack_support_shelf();

        // H1/H2-aligned screw bosses are intentionally optional. In the
        // current centered 40x40 mm L1 coil stack they collide with the coil
        // keepout, so the default enclosure relies on perimeter guidance.
        if (use_pcb_screw_bosses) {
          pcb_support_ribs();
        }

        if (use_stack_retention_ribs) {
          stack_retention_ribs();
        }
      }
}

module cup_contact_pad() {
  color([0.88, 0.68, 0.32, 1.0])
    maybe_cutaway()
      union() {
        // The TP-4 pad is cut to fit inside the centering rim. It is not tucked
        // under the rim, so the whole pad remains replaceable from above.
        cyl(pad_od, pad_th);

        // Optional future crown. The first TP-4 direct-pad trial keeps this
        // disabled because the purchased sheets are flat and thin.
        if (pad_crown_h > 0) {
          translate([0, 0, pad_th - 0.01])
            scale([1, 1, pad_crown_h / (pad_od / 2)])
              sphere(d = pad_od);
        }
      }
}

module aluminum_spreader() {
  color([0.75, 0.78, 0.80, 1.0])
    maybe_cutaway()
      cyl(spreader_od, spreader_th);
}

module flexible_heater() {
  color([0.78, 0.30, 0.16, 1.0])
    maybe_cutaway()
      cyl(heater_od, heater_th);

  // Four-wire heater/NTC cable drops internally to PCB pads.
  color([0.95, 0.95, 0.95, 1.0])
    translate([heater_cable_x - heater_cable_w / 2, heater_cable_y - heater_cable_d / 2, -heater_cable_drop_h])
      cube([heater_cable_w, heater_cable_d, heater_cable_drop_h + heater_th]);
}

module insulation_layer() {
  color([0.95, 0.92, 0.72, 1.0])
    maybe_cutaway()
      difference() {
        cyl(insulation_od, insulation_th);
        stack_retention_edge_slots(insulation_th);
        heater_cable_insulation_slot(insulation_th);
      }
}

module pcb_reference() {
  color([0.05, 0.45, 0.18, 1.0])
    maybe_cutaway()
      difference() {
        cyl(pcb_od, pcb_th);
        stack_retention_edge_slots(pcb_th);
        pcb_mounting_hole_cutouts(pcb_th);
      }
}

module ferrite_reference() {
  color([0.08, 0.08, 0.08, 1.0])
    maybe_cutaway()
      cyl(ferrite_od, ferrite_th);
}

module rx_coil_reference() {
  color([0.90, 0.52, 0.12, 1.0])
    maybe_cutaway()
      rounded_box(coil_x, coil_y, coil_corner_r, coil_th);
}

module f1_reference() {
  // STALE SMD-placeholder box (see f1_* dims). Real F1 is KSD9700-70 (C156512),
  // a phi 8.9 x 28 mm leaded can — this box must be reworked to that geometry.
  // JLCPCB heater assembly places F1 on the heater bottom side, opposite the
  // non-soldering adhesive side.
  color([0.05, 0.05, 0.05, 1.0])
    translate([f1_on_heater_x, f1_on_heater_y, f1_on_heater_z])
      rounded_box(f1_x, f1_y, f1_corner_r, f1_z);
}

module assembly() {
  explode = show_exploded ? explode_gap : 0;

  if (show_bottom_tray) {
    bottom_tray();
  }

  if (show_reference_stack) {
    if (show_rx_coil_reference) {
      translate([0, 0, z_coil + 1 * explode]) rx_coil_reference();
    }
    if (show_ferrite_reference) {
      translate([0, 0, z_ferrite + 2 * explode]) ferrite_reference();
    }
    if (show_pcb_reference) {
      translate([0, 0, z_pcb + 3 * explode]) pcb_reference();
    }
    if (show_insulation) {
      translate([0, 0, z_insulation + 4 * explode]) insulation_layer();
    }
    if (show_flexible_heater) {
      translate([0, 0, z_heater + 5 * explode]) flexible_heater();
      translate([0, 0, z_heater + 5 * explode]) f1_reference();
    }
    if (use_aluminum_spreader && show_aluminum_spreader) {
      translate([0, 0, z_spreader + 6 * explode]) aluminum_spreader();
    }
    if (show_cup_contact_pad) {
      translate([0, 0, z_pad + 7 * explode]) cup_contact_pad();
    }
  }

}

assembly();
