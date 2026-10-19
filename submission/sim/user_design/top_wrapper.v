`default_nettype none


module top_wrapper;

    // io[i] sits on the tile eFPGA_top binds to A_*_top[i]. IOBUF.EN is an
    // active-high output enable, so it takes the inverted oeb.
    wire [39:0] io_in, io_out, io_oeb;
    (* keep, BEL="X11Y0.A" *) IOBUF io39_i (
        .OUT(io_in[39]),
        .IN (io_out[39]),
        .EN (~io_oeb[39])
    );
    (* keep, BEL="X10Y0.A" *) IOBUF io38_i (
        .OUT(io_in[38]),
        .IN (io_out[38]),
        .EN (~io_oeb[38])
    );
    (* keep, BEL="X9Y0.A" *) IOBUF io37_i (
        .OUT(io_in[37]),
        .IN (io_out[37]),
        .EN (~io_oeb[37])
    );
    (* keep, BEL="X8Y0.A" *) IOBUF io36_i (
        .OUT(io_in[36]),
        .IN (io_out[36]),
        .EN (~io_oeb[36])
    );
    (* keep, BEL="X7Y0.A" *) IOBUF io35_i (
        .OUT(io_in[35]),
        .IN (io_out[35]),
        .EN (~io_oeb[35])
    );
    (* keep, BEL="X5Y0.A" *) IOBUF io34_i (
        .OUT(io_in[34]),
        .IN (io_out[34]),
        .EN (~io_oeb[34])
    );
    (* keep, BEL="X4Y0.A" *) IOBUF io33_i (
        .OUT(io_in[33]),
        .IN (io_out[33]),
        .EN (~io_oeb[33])
    );
    (* keep, BEL="X3Y0.A" *) IOBUF io32_i (
        .OUT(io_in[32]),
        .IN (io_out[32]),
        .EN (~io_oeb[32])
    );
    (* keep, BEL="X2Y0.A" *) IOBUF io31_i (
        .OUT(io_in[31]),
        .IN (io_out[31]),
        .EN (~io_oeb[31])
    );
    (* keep, BEL="X1Y0.A" *) IOBUF io30_i (
        .OUT(io_in[30]),
        .IN (io_out[30]),
        .EN (~io_oeb[30])
    );
    (* keep, BEL="X12Y1.A" *) IOBUF io29_i (
        .OUT(io_in[29]),
        .IN (io_out[29]),
        .EN (~io_oeb[29])
    );
    (* keep, BEL="X0Y1.A" *) IOBUF io28_i (
        .OUT(io_in[28]),
        .IN (io_out[28]),
        .EN (~io_oeb[28])
    );
    (* keep, BEL="X12Y2.A" *) IOBUF io27_i (
        .OUT(io_in[27]),
        .IN (io_out[27]),
        .EN (~io_oeb[27])
    );
    (* keep, BEL="X0Y2.A" *) IOBUF io26_i (
        .OUT(io_in[26]),
        .IN (io_out[26]),
        .EN (~io_oeb[26])
    );
    (* keep, BEL="X12Y3.A" *) IOBUF io25_i (
        .OUT(io_in[25]),
        .IN (io_out[25]),
        .EN (~io_oeb[25])
    );
    (* keep, BEL="X0Y3.A" *) IOBUF io24_i (
        .OUT(io_in[24]),
        .IN (io_out[24]),
        .EN (~io_oeb[24])
    );
    (* keep, BEL="X12Y4.A" *) IOBUF io23_i (
        .OUT(io_in[23]),
        .IN (io_out[23]),
        .EN (~io_oeb[23])
    );
    (* keep, BEL="X0Y4.A" *) IOBUF io22_i (
        .OUT(io_in[22]),
        .IN (io_out[22]),
        .EN (~io_oeb[22])
    );
    (* keep, BEL="X12Y5.A" *) IOBUF io21_i (
        .OUT(io_in[21]),
        .IN (io_out[21]),
        .EN (~io_oeb[21])
    );
    (* keep, BEL="X0Y5.A" *) IOBUF io20_i (
        .OUT(io_in[20]),
        .IN (io_out[20]),
        .EN (~io_oeb[20])
    );
    (* keep, BEL="X12Y6.A" *) IOBUF io19_i (
        .OUT(io_in[19]),
        .IN (io_out[19]),
        .EN (~io_oeb[19])
    );
    (* keep, BEL="X0Y6.A" *) IOBUF io18_i (
        .OUT(io_in[18]),
        .IN (io_out[18]),
        .EN (~io_oeb[18])
    );
    (* keep, BEL="X12Y7.A" *) IOBUF io17_i (
        .OUT(io_in[17]),
        .IN (io_out[17]),
        .EN (~io_oeb[17])
    );
    (* keep, BEL="X0Y7.A" *) IOBUF io16_i (
        .OUT(io_in[16]),
        .IN (io_out[16]),
        .EN (~io_oeb[16])
    );
    (* keep, BEL="X12Y8.A" *) IOBUF io15_i (
        .OUT(io_in[15]),
        .IN (io_out[15]),
        .EN (~io_oeb[15])
    );
    (* keep, BEL="X0Y8.A" *) IOBUF io14_i (
        .OUT(io_in[14]),
        .IN (io_out[14]),
        .EN (~io_oeb[14])
    );
    (* keep, BEL="X12Y9.A" *) IOBUF io13_i (
        .OUT(io_in[13]),
        .IN (io_out[13]),
        .EN (~io_oeb[13])
    );
    (* keep, BEL="X0Y9.A" *) IOBUF io12_i (
        .OUT(io_in[12]),
        .IN (io_out[12]),
        .EN (~io_oeb[12])
    );
    (* keep, BEL="X12Y10.A" *) IOBUF io11_i (
        .OUT(io_in[11]),
        .IN (io_out[11]),
        .EN (~io_oeb[11])
    );
    (* keep, BEL="X0Y10.A" *) IOBUF io10_i (
        .OUT(io_in[10]),
        .IN (io_out[10]),
        .EN (~io_oeb[10])
    );
    (* keep, BEL="X11Y11.A" *) IOBUF io9_i (
        .OUT(io_in[9]),
        .IN (io_out[9]),
        .EN (~io_oeb[9])
    );
    (* keep, BEL="X10Y11.A" *) IOBUF io8_i (
        .OUT(io_in[8]),
        .IN (io_out[8]),
        .EN (~io_oeb[8])
    );
    (* keep, BEL="X9Y11.A" *) IOBUF io7_i (
        .OUT(io_in[7]),
        .IN (io_out[7]),
        .EN (~io_oeb[7])
    );
    (* keep, BEL="X8Y11.A" *) IOBUF io6_i (
        .OUT(io_in[6]),
        .IN (io_out[6]),
        .EN (~io_oeb[6])
    );
    (* keep, BEL="X7Y11.A" *) IOBUF io5_i (
        .OUT(io_in[5]),
        .IN (io_out[5]),
        .EN (~io_oeb[5])
    );
    (* keep, BEL="X5Y11.A" *) IOBUF io4_i (
        .OUT(io_in[4]),
        .IN (io_out[4]),
        .EN (~io_oeb[4])
    );
    (* keep, BEL="X4Y11.A" *) IOBUF io3_i (
        .OUT(io_in[3]),
        .IN (io_out[3]),
        .EN (~io_oeb[3])
    );
    (* keep, BEL="X3Y11.A" *) IOBUF io2_i (
        .OUT(io_in[2]),
        .IN (io_out[2]),
        .EN (~io_oeb[2])
    );
    (* keep, BEL="X2Y11.A" *) IOBUF io1_i (
        .OUT(io_in[1]),
        .IN (io_out[1]),
        .EN (~io_oeb[1])
    );
    (* keep, BEL="X1Y11.A" *) IOBUF io0_i (
        .OUT(io_in[0]),
        .IN (io_out[0]),
        .EN (~io_oeb[0])
    );

    // No UserCLK in this fabric: the clock enters on pad 16 (W_IO X0Y7) and
    // reaches the LC clock spine through the SW_term global buffer.
    wire clk;
    (* keep, BEL="X0Y11.A" *) GBUF clk_buf_i (
        .IN (io_in[16]),
        .OUT(clk)
    );

    sequential_16bit_en top_i (
        .clk(clk),
        .io_in(io_in),
        .io_out(io_out),
        .io_oeb(io_oeb)
    );

endmodule
`default_nettype wire
