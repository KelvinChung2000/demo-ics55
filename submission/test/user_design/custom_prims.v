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

// Scalar ports: FABulous's nextpnr integration does not support vector BEL ports.
(* blackbox, keep *)
module MACC_8x8_20 (
    input CLK,
    input EN,
    input ACC_RST,
    input ACC_CI,
    output ACC_CO,
    input A0, A1, A2, A3, A4, A5, A6, A7,
    input B0, B1, B2, B3, B4, B5, B6, B7,
    input C0, C1, C2, C3, C4, C5, C6, C7, C8, C9, C10, C11, C12, C13, C14, C15, C16, C17, C18, C19,
    output Q0, Q1, Q2, Q3, Q4, Q5, Q6, Q7, Q8, Q9, Q10, Q11, Q12, Q13, Q14, Q15, Q16, Q17, Q18, Q19
);
    parameter A_REG = 0;
    parameter B_REG = 0;
    parameter C_REG = 0;
    parameter SIGN_EXT = 0;
    parameter ACC_SEL = 0;
    parameter ACC_OUT = 0;
    parameter CLK_INV = 0;
endmodule
