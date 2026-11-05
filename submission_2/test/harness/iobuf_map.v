// Pad cells onto this fabric's IO BEL, IOBUF, whose EN is an active-high output
// enable. Pass with -extra-map. Yosys 0.67 and newer insert the $__FABULOUS_*
// cells by default; older Yosys leaves IO_1_bidirectional_frame_config_pass
// cells under -iopad, a BEL this fabric does not have.
module \$__FABULOUS_IBUF (input PAD, output OUT);
    IOBUF _TECHMAP_REPLACE_ (.EN(1'b0), .OUT(OUT), .PAD(PAD));
endmodule

module \$__FABULOUS_OBUF (output PAD, input IN);
    IOBUF _TECHMAP_REPLACE_ (.IN(IN), .EN(1'b1), .PAD(PAD));
endmodule

module \$__FABULOUS_TBUF (output PAD, input IN, input EN);
    IOBUF _TECHMAP_REPLACE_ (.IN(IN), .EN(EN), .PAD(PAD));
endmodule

module \$__FABULOUS_IOBUF (inout PAD, output OUT, input IN, input EN);
    IOBUF _TECHMAP_REPLACE_ (.IN(IN), .EN(EN), .OUT(OUT), .PAD(PAD));
endmodule

module IO_1_bidirectional_frame_config_pass (input CLK, T, I, output Q, O, inout PAD);
    wire en;
    \$_NOT_ t_inv (.A(T), .Y(en));
    IOBUF _TECHMAP_REPLACE_ (.IN(I), .EN(en), .OUT(O), .PAD(PAD));
endmodule
