
//Warning: The primitive InPass4_frame_config_mux was added by FABulous automatically.
(* blackbox, keep *)
module InPass4_frame_config_mux (
    output O0,
    output O1,
    output O2,
    output O3,
    (* iopad_external_pin *)
    input I0,
    (* iopad_external_pin *)
    input I1,
    (* iopad_external_pin *)
    input I2,
    (* iopad_external_pin *)
    input I3,
    input CLK
);
    parameter I0_reg = 0;
    parameter I1_reg = 0;
    parameter I2_reg = 0;
    parameter I3_reg = 0;
endmodule

//Warning: The primitive OutPass4_frame_config_mux was added by FABulous automatically.
(* blackbox, keep *)
module OutPass4_frame_config_mux (
    input I0,
    input I1,
    input I2,
    input I3,
    (* iopad_external_pin *)
    output O0,
    (* iopad_external_pin *)
    output O1,
    (* iopad_external_pin *)
    output O2,
    (* iopad_external_pin *)
    output O3,
    input CLK
);
    parameter I0_reg = 0;
    parameter I1_reg = 0;
    parameter I2_reg = 0;
    parameter I3_reg = 0;
endmodule
