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

// A signal split into copies in RTL so that ABC, which buffers no net in an
// AREA strategy, derives each copy's complement separately. BUFX4H7L carries
// 0.097 pF; one copy drives at most 20 enable muxes.
module fanout_buf (input A, output X);
  BUFX4H7L _TECHMAP_REPLACE_ (.A(A), .Y(X));
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

// The same disease on the MACC: each Q bit feeds about 40 switch-matrix mux
// inputs, 0.09 to 0.12 pF once routed, and ABC drove it from an OAI22X0P5.
// The guard is FABULOUS_LC_drive's, on NoConfigBits: MACC_bot instantiates
// the BEL with no parameter, so only a cell this rule made carries one.
(* techmap_celltype = "MACC_8x8_20" *)
module MACC_8x8_20_drive (CLK, EN, ACC_RST, ACC_CI, ACC_CO, A, B, C, Q, ConfigBits);
  localparam CONFIG_WIDTH = 7;
  parameter NoConfigBits = 0;
  parameter _TECHMAP_BITS_CONNMAP_ = 0;
  parameter _TECHMAP_CONNMAP_A_ = 0;
  parameter _TECHMAP_CONNMAP_B_ = 0;
  parameter _TECHMAP_CONNMAP_C_ = 0;
  parameter _TECHMAP_CONNMAP_Q_ = 0;
  parameter _TECHMAP_CONNMAP_ConfigBits_ = 0;
  input CLK, EN, ACC_RST, ACC_CI;
  output ACC_CO;
  input [7:0] A, B;
  input [19:0] C;
  output [19:0] Q;
  input [CONFIG_WIDTH-1:0] ConfigBits;
  generate
    if (_TECHMAP_BITS_CONNMAP_ != 0 && (
        $bits(_TECHMAP_CONNMAP_A_) != 8 * _TECHMAP_BITS_CONNMAP_ ||
        $bits(_TECHMAP_CONNMAP_B_) != 8 * _TECHMAP_BITS_CONNMAP_ ||
        $bits(_TECHMAP_CONNMAP_C_) != 20 * _TECHMAP_BITS_CONNMAP_ ||
        $bits(_TECHMAP_CONNMAP_Q_) != 20 * _TECHMAP_BITS_CONNMAP_ ||
        $bits(_TECHMAP_CONNMAP_ConfigBits_) != CONFIG_WIDTH * _TECHMAP_BITS_CONNMAP_))
      $error("MACC_8x8_20 ports differ from MACC_8x8_20_drive in techmap/ics55_models.v");
  endgenerate
  wire _TECHMAP_FAIL_ = NoConfigBits != 0;
  wire [19:0] Q_bel;
  (* techmap_chtype = "MACC_8x8_20" *)
  _TECHMAP_PLACEHOLDER_ #(.NoConfigBits(CONFIG_WIDTH)) _TECHMAP_REPLACE_ (
    .CLK(CLK), .EN(EN), .ACC_RST(ACC_RST), .ACC_CI(ACC_CI), .ACC_CO(ACC_CO),
    .A(A), .B(B), .C(C), .Q(Q_bel), .ConfigBits(ConfigBits)
  );
  genvar i;
  generate
    for (i = 0; i < 20; i = i + 1) begin : Q_drive
      BUFX8H7L buffer (.A(Q_bel[i]), .Y(Q[i]));
    end
  endgenerate
endmodule

// MACC_bot's strobe_outbuf drives MACC_top's FrameStrobe port across the
// 168 um supertile, and every MACC_top configuration latch hangs on that port
// net: 34 latch G pins and 0.07 to 0.08 pF per strobe, against BUFX1H7L's
// 0.035 pF. A BUFX5H7L (0.122 pF, the area of a BUFX4) in front of the
// ConfigMem leaves the outbuf driving two inputs. The guard is on
// MaxFramesPerCol, which MACC_top does not set.
(* techmap_celltype = "MACC_top_ConfigMem" *)
module MACC_top_ConfigMem_strobe (FrameData, FrameStrobe, ConfigBits, ConfigBits_N);
  localparam FRAMES = 20;
  localparam CONFIG_WIDTH = 406;
  parameter MaxFramesPerCol = 0;
  parameter _TECHMAP_BITS_CONNMAP_ = 0;
  parameter _TECHMAP_CONNMAP_FrameData_ = 0;
  parameter _TECHMAP_CONNMAP_FrameStrobe_ = 0;
  parameter _TECHMAP_CONNMAP_ConfigBits_ = 0;
  parameter _TECHMAP_CONNMAP_ConfigBits_N_ = 0;
  input [31:0] FrameData;
  input [FRAMES-1:0] FrameStrobe;
  output [CONFIG_WIDTH-1:0] ConfigBits, ConfigBits_N;
  generate
    if (_TECHMAP_BITS_CONNMAP_ != 0 && (
        $bits(_TECHMAP_CONNMAP_FrameData_) != 32 * _TECHMAP_BITS_CONNMAP_ ||
        $bits(_TECHMAP_CONNMAP_FrameStrobe_) != FRAMES * _TECHMAP_BITS_CONNMAP_ ||
        $bits(_TECHMAP_CONNMAP_ConfigBits_) != CONFIG_WIDTH * _TECHMAP_BITS_CONNMAP_ ||
        $bits(_TECHMAP_CONNMAP_ConfigBits_N_) != CONFIG_WIDTH * _TECHMAP_BITS_CONNMAP_))
      $error("MACC_top_ConfigMem ports differ from MACC_top_ConfigMem_strobe in techmap/ics55_models.v");
  endgenerate
  wire _TECHMAP_FAIL_ = MaxFramesPerCol != 0;
  wire [FRAMES-1:0] strobe;
  genvar i;
  generate
    for (i = 0; i < FRAMES; i = i + 1) begin : strobe_drive
      BUFX5H7L buffer (.A(FrameStrobe[i]), .Y(strobe[i]));
    end
  endgenerate
  (* techmap_chtype = "MACC_top_ConfigMem" *)
  _TECHMAP_PLACEHOLDER_ #(.MaxFramesPerCol(FRAMES)) _TECHMAP_REPLACE_ (
    .FrameData(FrameData), .FrameStrobe(strobe), .ConfigBits(ConfigBits),
    .ConfigBits_N(ConfigBits_N)
  );
endmodule

module cus_mux21 (A0, A1, S, X);
  input A0, A1, S;
  output X;
  MUX2X1H7L _TECHMAP_REPLACE_ (.A(A0), .B(A1), .S0(S), .Y(X));
endmodule
