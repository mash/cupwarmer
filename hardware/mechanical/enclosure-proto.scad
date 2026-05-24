// Cupwarmer v1 enclosure prototype.
// Units: millimeters.
//
// This is a mechanical study model, not a production CAD source.
// It captures the current enclosure intent:
// - no cup-contact metal
// - hidden internal aluminum spreader
// - single-piece resin bottom tray with integrated low retaining lip
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

show_bottom_tray = true;
show_cup_contact_pad = true;
show_aluminum_spreader = true;
show_flexible_heater = true;
show_insulation = true;
show_pcb_reference = true;
show_ferrite_reference = true;
show_rx_coil_reference = true;

/* [Quality] */

$fn = 128;

// Main envelope.
enclosure_od = 60.0;
wall = 1.6;
bottom_floor_th = 1.0;
lip_below_pad = 0.25;
integrated_lip_h = 1.15;
integrated_lip_inner_od = 55.6;
spreader_pocket_od = 55.2;
spreader_pocket_depth = 0.45;

// Functional round parts.
pcb_od = 56.0;
pcb_th = 1.0;
heater_od = 56.0;
heater_th = 0.35;
spreader_od = 54.5;
spreader_th = 0.30;
pad_od = 56.5;
pad_th = 0.80;
pad_crown_h = 0.45;

// Qi reference stack.
// L1: Wuerth Elektronik 760308102207, WE-WPCC Qi RX coil.
// Datasheet size: 40x40x1.2 mm rounded square, visible corner radius about 5-8 mm.
coil_x = 40.0;
coil_y = 40.0;
coil_corner_r = 6.0;
coil_th = 1.20;
ferrite_od = 56.0;
ferrite_th = 0.50;
insulation_od = 56.0;
insulation_th = 0.70;
f1_clearance_gap = 5.6;

// Assembly clearances.
radial_clearance = 0.35;
tray_inner_od = enclosure_od - 2 * wall;
pcb_clear_od = pcb_od + 2 * radial_clearance;
heater_clear_od = heater_od + 2 * radial_clearance;

// Z positions in assembled view.
z_bottom_floor_top = bottom_floor_th;
z_coil = z_bottom_floor_top + 0.20;
z_ferrite = z_coil + coil_th + 0.20;
z_pcb = z_ferrite + ferrite_th + 0.35;
z_insulation = z_pcb + pcb_th + 0.25;
z_heater = z_insulation + insulation_th + f1_clearance_gap;
z_spreader = z_heater + heater_th;
z_pad = z_spreader + spreader_th;
z_ring = z_spreader - 0.20;
bottom_tray_h = z_pad + pad_th - lip_below_pad;
z_lip_pocket_bottom = z_spreader - spreader_pocket_depth;

// Heater cable drops internally from the heater underside to PCB pads.
// Heater J1 pads in hardware/kicad/heater/heater.kicad_pcb are centered at
// (100, 122.5), i.e. (0, +22.5) relative to the 56 mm heater board center.
heater_cable_x = 0.0;
heater_cable_y = 22.5;
heater_cable_w = 24.0;
heater_cable_d = 5.0;
heater_cable_drop_h = z_heater - (z_pcb + pcb_th);
heater_cable_slot_clearance = 0.40;

// F1: Xucheng KSD9700-70/5JSB/080C/QG, LCSC C156512.
// C156512 drawing: iron shell, 20.0 mm body length, 8.9 mm max width,
// 5.1 mm max thickness. Leads are 80 +/-3 mm with 8 +/-1 mm stripped/tinned.
// JLCPCB flexible-heater service will include the thermostat switch in the
// heater assembly. With 3M 468MP on the non-soldering side, F1 is modeled on
// the heater bottom side, away from the spreader adhesive bond.
f1_x = 20.0;
f1_y = 8.9;
f1_z = 5.1;
f1_corner_r = 1.5;
f1_on_heater_x = 0;
f1_on_heater_y = -14.0;
f1_on_heater_z = -f1_z;

// PCB support. The original H3/H4/H5 mounting holes land inside the 40x40 mm
// L1 coil envelope, so the enclosure supports the PCB by six small ribs from
// the wall instead of through-board bosses or a full annular shelf.
pcb_support_rib_count = 6;
pcb_support_rib_w = 5.0;
pcb_support_rib_depth = 2.4;
pcb_support_outer_r = pcb_clear_od / 2;
pcb_support_inner_r = pcb_support_outer_r - pcb_support_rib_depth;
pcb_support_z = bottom_floor_th;
pcb_support_h = z_pcb - bottom_floor_th;

// Taller stack retention ribs. These are molded with the bottom tray and pass
// through local PCB/insulation edge notches. They act as perimeter datum ribs
// for the heater/spreader stack, not as hard clamps on the heater.
stack_retention_rib_count = 4;
stack_retention_rib_angle0 = 45;
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
          cyl(enclosure_od, bottom_tray_h);

          // Internal ledge under the heat stack. It also acts as a drip break.
          translate([0, 0, bottom_tray_h - 0.70])
            annulus(enclosure_od - 1.2, heater_clear_od, 0.70);

          // Main cavity. The bottom floor stays solid and thin for Qi coupling.
          translate([0, 0, bottom_floor_th])
            cyl(tray_inner_od, bottom_tray_h + 0.20);

          // Clearance for a 56 mm PCB/heater stack inside a 60 mm enclosure.
          translate([0, 0, bottom_floor_th])
            cyl(pcb_clear_od, bottom_tray_h + 0.20);

          // Bottom anti-slip ring groove.
          translate([0, 0, -0.05])
            annulus(enclosure_od - 3.0, enclosure_od - 6.0, 0.45);
        }

        // Six local support ribs rise from the bottom floor and support the
        // PCB outer edge. The center remains open for L1/ferrite keepout.
        for (i = [0 : pcb_support_rib_count - 1]) {
          rotate([0, 0, i * 360 / pcb_support_rib_count + 30])
            translate([pcb_support_inner_r, -pcb_support_rib_w / 2, pcb_support_z])
              cube([pcb_support_rib_depth, pcb_support_rib_w, pcb_support_h]);
        }

        stack_retention_ribs();
        integrated_retaining_lip();
      }
}

module integrated_retaining_lip() {
  lip_z = z_pad + pad_th - integrated_lip_h - lip_below_pad;
  color([0.12, 0.12, 0.12, 1.0])
    union() {
      translate([0, 0, lip_z])
        annulus(enclosure_od, integrated_lip_inner_od, integrated_lip_h);

      // Pocket wall hides the aluminum spreader edge while keeping the cup
      // contact crown proud of the enclosure.
      translate([0, 0, z_lip_pocket_bottom])
        annulus(enclosure_od - 0.8, spreader_pocket_od, spreader_pocket_depth);
    }
}

module cup_contact_pad() {
  color([0.88, 0.68, 0.32, 0.65])
    maybe_cutaway()
      union() {
        cyl(pad_od, pad_th);

        // Slight convex crown for concave cup bottoms. The retaining ring
        // intentionally stays below this surface so it does not create a
        // cup-facing recess.
        translate([0, 0, pad_th - 0.01])
          scale([1, 1, pad_crown_h / (pad_od / 2)])
            sphere(d = pad_od);
      }
}

module aluminum_spreader() {
  color([0.75, 0.78, 0.80, 0.85])
    maybe_cutaway()
      cyl(spreader_od, spreader_th);
}

module flexible_heater() {
  color([0.78, 0.30, 0.16, 0.70])
    maybe_cutaway()
      cyl(heater_od, heater_th);

  // Four-wire heater/NTC cable drops internally to PCB pads.
  color([0.95, 0.95, 0.95, 0.80])
    translate([heater_cable_x - heater_cable_w / 2, heater_cable_y - heater_cable_d / 2, -heater_cable_drop_h])
      cube([heater_cable_w, heater_cable_d, heater_cable_drop_h + heater_th]);
}

module insulation_layer() {
  color([0.95, 0.92, 0.72, 0.55])
    maybe_cutaway()
      difference() {
        cyl(insulation_od, insulation_th);
        stack_retention_edge_slots(insulation_th);
        heater_cable_insulation_slot(insulation_th);
      }
}

module pcb_reference() {
  color([0.05, 0.45, 0.18, 0.65])
    maybe_cutaway()
      difference() {
        cyl(pcb_od, pcb_th);
        stack_retention_edge_slots(pcb_th);
      }
}

module ferrite_reference() {
  color([0.08, 0.08, 0.08, 0.70])
    maybe_cutaway()
      cyl(ferrite_od, ferrite_th);
}

module rx_coil_reference() {
  color([0.90, 0.52, 0.12, 0.70])
    maybe_cutaway()
      rounded_box(coil_x, coil_y, coil_corner_r, coil_th);
}

module f1_reference() {
  // KSD9700 C156512 iron-shell body envelope. JLCPCB heater assembly places
  // this on the heater bottom side, opposite the non-soldering adhesive side.
  color([0.05, 0.05, 0.05, 0.85])
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
    if (show_aluminum_spreader) {
      translate([0, 0, z_spreader + 6 * explode]) aluminum_spreader();
    }
    if (show_cup_contact_pad) {
      translate([0, 0, z_pad + 7 * explode]) cup_contact_pad();
    }
  }

}

assembly();
