// The port declaration of the ECOS Factory macro, copied from the package's own
// `verilog/ics55_ecos_sram_512x32_m4_stub.v` and marked for Yosys.
//
// It exists because the ECC flow builds its workspace by running synthesis, and
// the macro's LEF and liberty can only be appended to the workspace database
// after that workspace exists. Yosys therefore never sees the liberty for this
// cell and would refuse an undeclared module; every step after synthesis reads
// the real views. Keep the port list byte-identical to the vendor stub.
//
// Package: openecos-projects/ics55_ecos_sram, release
// sram-v1-71fed9dc… asset `ics55_ecos_sram_512x32_m4.tar.gz`. The LEF and the
// ss1p08v125ccmax liberty of that package are vendored beside this file.
(* blackbox *)
module ics55_ecos_sram_512x32_m4 (
    MAR,
    D,
    Q,
    MARE,
    GWEB,
    A,
    WEB,
    CLK,
    CEB
  );

  input [8:0] A;
  input CEB;
  input CLK;
  input [31:0] D;
  input GWEB;
  input [3:0] MAR;
  input MARE;
  input [31:0] WEB;
  output [31:0] Q;

endmodule
