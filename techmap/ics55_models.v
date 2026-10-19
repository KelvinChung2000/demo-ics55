// Yosys techmap rules binding FABulous model primitives to ICS55 cells.
//
// `Fabric/models_pack.v` writes `my_buf` as a continuous assignment carrying
// `(* keep *)`. That attribute stops `opt_clean` removing instances, but it is
// not `keep_hierarchy` and does not stop `flatten`, and an assignment leaves no
// cell behind once flattened. Every one of a tile's boundary buffers therefore
// collapsed into a net alias. Mapping them to a real cell first is what keeps
// them, and it has to run before the flatten in ECC's synthesis script.
//
// Applied through YOSYS_TECHMAP_FILES, which flow/project.py sets.

// Drive strength here is what gets placed: flow/project.py skips TimingOpt,
// because Sizer is not installed, so nothing resizes these afterwards. X1 costs
// no more area than a weaker one, BUFX0P5 through BUFX1 all being 1.12 um^2.
// H7L matches the threshold flavour the sequential cells map to in these tiles.
module my_buf (input A, output X);
  BUFX1H7L _TECHMAP_REPLACE_ (.A(A), .Y(X));
endmodule

// The tile flow's CTS builds no tree, so these two are the whole clock network.
// ICS55 has no dedicated clock buffer, and ECC's own CTS list for it starts at
// BUFX8H7L. MACC_8x8_20 drives its 56 registers through clk_buf, 0.111 pF once
// routed, past BUFX4H7L's 0.097 pF max_capacitance.
module clk_buf (input A, output X);
  BUFX8H7L _TECHMAP_REPLACE_ (.A(A), .Y(X));
endmodule

// flow/project.py puts one on every GBUF feedthrough, so each hop drives one
// tile, about 0.003 pF against BUFX3H7L's 0.073 pF. BUFX3 costs what BUFX2 does
// and 0.56 um^2 less than BUFX4, which SW_term at 0.989 placeable needs.
module clk_hop (input A, output X);
  BUFX3H7L _TECHMAP_REPLACE_ (.A(A), .Y(X));
endmodule

// ABC reaches most of these on its own but not all of them, and it pays for
// the ones it misses twice: a 4:1 built from three MUX2X1 costs 8.4 um^2
// against MUX4X1's 6.44, and the select complements stay live because the
// decomposed form still reads them. Mapping directly took LUT4x8_ha from 312
// mapped 4:1s to 380 and from 29 inverters to 3.
//
// The encodings agree: the cell is A on S1S0 = 00 through D on 11, which is
// A0 through A3 here. cus_mux81 and cus_mux161 are built from cus_mux41, so
// this rule reaches inside them too.
module cus_mux41 (A0, A1, A2, A3, S0, S0N, S1, S1N, X);
  input A0, A1, A2, A3, S0, S0N, S1, S1N;
  output X;
  // S0N and S1N are complements the caller derives and the cell does not
  // take, so they go unread here and whatever drove them is cleaned up.
  MUX4X1H7L _TECHMAP_REPLACE_ (.A(A0), .B(A1), .C(A2), .D(A3), .S0(S0), .S1(S1), .Y(X));
endmodule

// A LUT4x8_ha LC output feeds about 40 switch-matrix mux inputs, 0.09 to 0.10
// pF once routed. ABC sees that net as a primary output carrying only abc_load,
// so it drives it with an X0P5 cell whose max_capacitance is 0.011 to 0.024 pF,
// and nothing after synthesis resizes it. BUFX8H7L's limit is 0.192 pF.
//
// The replacement LC is placed as a placeholder retyped to FABULOUS_LC with K
// set to its default 4, so it is still K=4 logic once flattened. `hierarchy`
// has already turned every parameterised instance into a $paramod type, so a
// plain FABULOUS_LC cell carrying K can only be one this rule made, and the
// rule refuses it rather than wrapping it again.
(* techmap_celltype = "FABULOUS_LC" *)
module FABULOUS_LC_drive (I, O, Ci, Co, SR, EN, CLK, ConfigBits);
  localparam I_WIDTH = 4;
  localparam CONFIG_WIDTH = 19;
  parameter K = 0;
  parameter _TECHMAP_BITS_CONNMAP_ = 0;
  parameter _TECHMAP_CONNMAP_I_ = 0;
  parameter _TECHMAP_CONNMAP_ConfigBits_ = 0;
  input [I_WIDTH-1:0] I;
  output O;
  input Ci;
  output Co;
  input SR, EN, CLK;
  input [CONFIG_WIDTH-1:0] ConfigBits;
  // techmap pads or truncates a port whose width differs from the cell's.
  generate
    if (_TECHMAP_BITS_CONNMAP_ != 0 && (
        $bits(_TECHMAP_CONNMAP_I_) != I_WIDTH * _TECHMAP_BITS_CONNMAP_ ||
        $bits(_TECHMAP_CONNMAP_ConfigBits_) != CONFIG_WIDTH * _TECHMAP_BITS_CONNMAP_))
      $error("FABULOUS_LC ports differ from FABULOUS_LC_drive in techmap/ics55_models.v");
  endgenerate
  wire _TECHMAP_FAIL_ = K != 0;
  wire O_lc;
  (* techmap_chtype = "FABULOUS_LC" *)
  _TECHMAP_PLACEHOLDER_ #(.K(4)) _TECHMAP_REPLACE_ (
    .I(I), .O(O_lc), .Ci(Ci), .Co(Co), .SR(SR), .EN(EN), .CLK(CLK),
    .ConfigBits(ConfigBits)
  );
  BUFX8H7L _TECHMAP_REPLACE_.O_drive (.A(O_lc), .Y(O));
endmodule

module cus_mux21 (A0, A1, S, X);
  input A0, A1, S;
  output X;
  MUX2X1H7L _TECHMAP_REPLACE_ (.A(A0), .B(A1), .S0(S), .Y(X));
endmodule
