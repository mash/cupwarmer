// Cupwarmer v1 enclosure prototype.
// Units: millimeters.
//
// This is a mechanical study model, not a production CAD source.
// It captures the current enclosure intent:
// - no cup-contact metal
// - hidden internal aluminum spreader
// - two-piece resin enclosure: bottom tray + top retaining ring
// - radial heater pigtail exit
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
show_top_retaining_ring = true;
show_cup_contact_pad = true;
show_aluminum_spreader = true;
show_flexible_heater = true;
show_f1_reference = true;
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
bottom_tray_h = 6.2;
top_ring_h = 1.8;
top_ring_wall = 1.5;
top_ring_overlap = 1.0;
top_ring_below_pad = 0.25;

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
z_heater = z_insulation + insulation_th;
z_spreader = z_heater + heater_th;
z_pad = z_spreader + spreader_th;
z_ring = z_spreader - 0.20;

// Pigtail channel.
pigtail_angle = 0;
pigtail_w = 7.0;
pigtail_h = 2.0;
pigtail_z = z_heater - 0.35;

// PCB support. The original H3/H4/H5 mounting holes land inside the
// 40x40 mm L1 coil envelope, so the enclosure supports the PCB by its
// outer edge instead of using through-board bosses.
pcb_support_lip_w = 2.2;
pcb_support_th = 0.30;
pcb_support_outer_od = pcb_clear_od;
pcb_support_inner_od = pcb_od - 2 * pcb_support_lip_w;
pcb_support_z = z_pcb - pcb_support_th;

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

module pigtail_channel_cut() {
  rotate([0, 0, pigtail_angle])
    translate([enclosure_od / 2 - wall - 1.0, -pigtail_w / 2, pigtail_z])
      cube([wall + 4.0, pigtail_w, pigtail_h]);
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

          // Radial heater harness exit.
          pigtail_channel_cut();

          // Bottom anti-slip ring groove.
          translate([0, 0, -0.05])
            annulus(enclosure_od - 3.0, enclosure_od - 6.0, 0.45);
        }

        // Thin perimeter ledge supporting only the PCB outer edge.
        // The center remains open for L1/ferrite keepout.
        translate([0, 0, pcb_support_z])
          annulus(pcb_support_outer_od, pcb_support_inner_od, pcb_support_th);
      }
}

module top_retaining_ring() {
  inner_opening = pad_od - 2 * top_ring_overlap;
  color([0.12, 0.12, 0.12, 1.0])
    maybe_cutaway()
      difference() {
        union() {
          annulus(enclosure_od, inner_opening, top_ring_h);

          // Downward skirt hides the aluminum spreader edge.
          translate([0, 0, -0.80])
            annulus(enclosure_od, spreader_od + 1.2, 0.80);
        }

        // Soft bevel-like clearance for the exposed silicone pad.
        translate([0, 0, top_ring_h - 0.35])
          cyl(pad_od - 0.4, 0.50);

        // Match the pigtail side relief.
        rotate([0, 0, pigtail_angle])
          translate([enclosure_od / 2 - wall - 1.0, -pigtail_w / 2, -1.0])
            cube([wall + 4.0, pigtail_w, top_ring_h + 2.0]);
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

  // Four-wire heater/NTC pigtail reference envelope.
  color([0.95, 0.95, 0.95, 0.80])
    rotate([0, 0, pigtail_angle])
      translate([heater_od / 2 - 1.5, -2.2, heater_th / 2 - 0.35])
        cube([11.0, 4.4, 0.70]);
}

module insulation_layer() {
  color([0.95, 0.92, 0.72, 0.55])
    maybe_cutaway()
      cyl(insulation_od, insulation_th);
}

module pcb_reference() {
  color([0.05, 0.45, 0.18, 0.65])
    maybe_cutaway()
      cyl(pcb_od, pcb_th);
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
  // Approximate KSD9700 body envelope. Position is intentionally off-center
  // and outside the coil core region, pending real body dimensions.
  color([0.05, 0.05, 0.05, 0.85])
    translate([14, 0, 0.55])
      rotate([0, 90, 0])
        cylinder(d = 4.2, h = 12.0, center = true, $fn = 48);
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
    }
    if (show_f1_reference) {
      translate([0, 0, z_heater + 5 * explode]) f1_reference();
    }
    if (show_aluminum_spreader) {
      translate([0, 0, z_spreader + 6 * explode]) aluminum_spreader();
    }
    if (show_cup_contact_pad) {
      translate([0, 0, z_pad + 7 * explode]) cup_contact_pad();
    }
  }

  if (show_top_retaining_ring) {
    translate([0, 0, z_pad + pad_th - top_ring_h - top_ring_below_pad + 8 * explode])
      top_retaining_ring();
  }
}

assembly();
