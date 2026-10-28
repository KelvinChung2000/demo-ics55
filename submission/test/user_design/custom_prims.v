// Yosys blackboxes for the fabric BELs that synth_fabulous's prims.v lacks, in
// the form FABulous's addBelsToPrim emits (ConfigBits become parameters).

(* blackbox, keep *)
module IOBUF (
    input CLK,
    input IN,
    input EN,
    output OUT,
    (* iopad_external_pin *)
    output IN_top,
    (* iopad_external_pin *)
    output EN_top,
    (* iopad_external_pin *)
    input OUT_top,
    // Pad side of the -iopad cell iobuf_map.v replaces; nextpnr binds a PCF set_io through it.
    (* iopad_external_pin *)
    inout PAD
);
    parameter EN_REG = 0;
    parameter IN_REG = 0;
    parameter OUT_REG = 0;
endmodule

(* blackbox, keep *)
module GBUF (
    input IN,
    output OUT
);
    parameter INVERT = 0;
endmodule

// RESET_top is the USER_RESET pad; a wrapper takes the pad through RESET only.
(* blackbox, keep *)
module SYS_RESET (
    output RESET,
    (* iopad_external_pin *)
    input RESET_top
);
endmodule

// CLOCK_top is the USER_CLK pad; a wrapper takes the pad through CLOCK only.
(* blackbox, keep *)
module USER_CLK (
    output CLOCK,
    (* iopad_external_pin *)
    input CLOCK_top
);
endmodule
