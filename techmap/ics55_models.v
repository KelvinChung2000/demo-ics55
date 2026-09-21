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

module cus_mux21 (A0, A1, S, X);
  input A0, A1, S;
  output X;
  MUX2X1H7L _TECHMAP_REPLACE_ (.A(A0), .B(A1), .S0(S), .Y(X));
endmodule
