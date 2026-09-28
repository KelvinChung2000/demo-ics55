`default_nettype none

// Write-only SPI mode 0 slave: the host shifts 32-bit words in MSB first while
// spi_cs_n is low, and each complete word gives a one-cycle strobe. There is
// no MISO. As in bitbang.v, SCK, CS and MOSI are oversampled in the clk
// domain, so SCK never clocks a flop.
//
// Timing, in clk periods T:
// - SCK high and low must each last longer than T, so f_clk > 2 f_sck is the
//   hard bound. Run at f_clk >= 4 f_sck (each phase >= 2T), which keeps a
//   whole T of margin for synchroniser skew.
// - CS must fall more than 2T before the first SCK rise and stay high more
//   than 2T between frames.
// - CS must stay low until the last SCK fall, as mode 0 requires. CS and SCK
//   pass through equal synchroniser depths, so active then still covers the
//   strobe cycle; a CS release while SCK is high can lose the last word.
// - A partial word is dropped when CS rises.
module config_spi (
    input wire spi_sck,
    input wire spi_cs_n,
    input wire spi_mosi,
    output reg strobe,
    output reg [31:0] data,
    output wire active,
    input wire clk,
    input wire reset_n
);

    reg [3:0] sck_sample;
    reg [3:0] cs_n_sample;
    reg [3:0] mosi_sample;

    reg [30:0] shift;
    reg [4:0] bit_count;

    wire selected = !cs_n_sample[3];
    wire sck_rise = !sck_sample[3] && sck_sample[2];

    assign active = selected;

    always @(posedge clk, negedge reset_n) begin : p_input_sync
        if (!reset_n) begin
            sck_sample  <= 4'b0000;
            cs_n_sample <= 4'b1111;
            mosi_sample <= 4'b0000;
        end else begin
            sck_sample  <= {sck_sample[2:0], spi_sck};
            cs_n_sample <= {cs_n_sample[2:0], spi_cs_n};
            mosi_sample <= {mosi_sample[2:0], spi_mosi};
        end
    end

    always @(posedge clk, negedge reset_n) begin : p_shift
        if (!reset_n) begin
            shift <= 31'b0;
            bit_count <= 5'd0;
            data <= 32'b0;
            strobe <= 1'b0;
        end else begin
            strobe <= 1'b0;
            if (!selected) begin
                bit_count <= 5'd0;
            end else if (sck_rise) begin
                // mosi_sample[3] is the last sample before the edge, as in bitbang.v
                bit_count <= bit_count + 5'd1;
                if (bit_count == 5'd31) begin
                    data <= {shift, mosi_sample[3]};
                    strobe <= 1'b1;
                end else begin
                    shift <= {shift[29:0], mosi_sample[3]};
                end
            end
        end
    end

endmodule
`resetall
