// Post-route simulation models for the cells nextpnr-generic --write emits for
// the FABulous uarch. Each specify path or check is an SDF annotation target
// with zero delay until $sdf_annotate fills it.
`timescale 1ps / 1ps

module FABULOUS_LC #(
    parameter [15:0] INIT = 16'h0000,
    parameter FF = 0,
    parameter SET_NORESET = 0,
    parameter ASYNC_SR = 0,
    parameter NEG_CLK = 0,
    parameter I0MUX = 0
) (
    input  I0, I1, I2, I3,
    input  CLK, EN, SR,
    output O,
    output reg Q
);
    // The fabric LC (../rtl/primitives/FABULOUS_LC/fabulous/FABULOUS_LC.v) has a
    // posedge flop with synchronous SR over EN. The carry input is not modelled.
    initial if (ASYNC_SR || NEG_CLK || I0MUX)
        $fatal(1, "%m: ASYNC_SR, NEG_CLK and I0MUX have no fabric support");

    // nextpnr's packer leaves EN and SR unconnected for a plain flop, meaning
    // EN=1 and SR=0 (generic/viaduct/fabulous/pack.cc, prepare_ffs).
    wire en = (EN === 1'bz) ? 1'b1 : EN;
    wire sr = (SR === 1'bz) ? 1'b0 : SR;
    // A ?: mux tree, as in the fabric LUT, so an unconnected (z) input gives
    // a known output when INIT does not depend on it and x when it does.
    wire [7:0] s3 = I3 ? INIT[15:8] : INIT[7:0];
    wire [3:0] s2 = I2 ? s3[7:4] : s3[3:0];
    wire [1:0] s1 = I1 ? s2[3:2] : s2[1:0];
    wire lut = I0 ? s1[1] : s1[0];
    assign O = lut;

    always @(posedge CLK)
        if (sr) Q <= SET_NORESET;
        else if (en) Q <= lut;

    specify
        (I0 => O) = 0;
        (I1 => O) = 0;
        (I2 => O) = 0;
        (I3 => O) = 0;
        (CLK => Q) = 0;
        $setuphold(posedge CLK, I0, 0, 0);
        $setuphold(posedge CLK, I1, 0, 0);
        $setuphold(posedge CLK, I2, 0, 0);
        $setuphold(posedge CLK, I3, 0, 0);
        $setuphold(posedge CLK, EN, 0, 0);
        $setuphold(posedge CLK, SR, 0, 0);
    endspecify
endmodule

// The pad side is a reg the testbench drives or reads hierarchically, since the
// routed netlist has no top-level ports.
module IOBUF (
    input  IN,
    input  EN,
    output OUT
);
    reg pad_drive;
    assign OUT = pad_drive;
    specify
        (IN => OUT) = 0;
    endspecify
endmodule

module GBUF #(
    parameter INVERT = 0
) (
    input  IN,
    output OUT
);
    assign OUT = INVERT ? ~IN : IN;
    specify
        (IN => OUT) = 0;
    endspecify
endmodule

module USER_CLK (
    output CLOCK
);
    reg pad_drive;
    assign CLOCK = pad_drive;
endmodule

module SYS_RESET (
    output RESET
);
    reg pad_drive;
    assign RESET = pad_drive;
endmodule

module _CONST0_DRV (
    output O
);
    assign O = 1'b0;
endmodule

module _CONST1_DRV (
    output O
);
    assign O = 1'b1;
endmodule
