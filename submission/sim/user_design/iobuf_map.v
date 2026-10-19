// synth_fabulous -iopad leaves IO_1_bidirectional_frame_config_pass cells, a BEL
// this fabric does not have; its IO BEL is IOBUF, whose EN is an active-high
// output enable. Pass with -extra-map after -iopad.
module IO_1_bidirectional_frame_config_pass (input CLK, T, I, output Q, O, inout PAD);
    wire en;
    \$_NOT_ t_inv (.A(T), .Y(en));
    IOBUF _TECHMAP_REPLACE_ (.IN(I), .EN(en), .OUT(O), .PAD(PAD));
endmodule
