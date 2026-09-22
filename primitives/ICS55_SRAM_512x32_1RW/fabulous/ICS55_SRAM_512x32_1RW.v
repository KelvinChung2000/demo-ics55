// Copyright 2026 FABulous Contributors
// Copyright 2025 Leo Moser
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// The block-RAM BEL of Tile/E_BRAM, adapted from the classic library's
// IHP_SRAM_1024x32_1RW. Two differences from that one, and both are structural.
//
// The ICS55 macro is instantiated here rather than brought out on EXTERNAL
// ports, because this fabric abuts hardened tiles and the memory has to sit
// inside the block-RAM column rather than beside the array.
//
// `ics55_ecos_sram_512x32_m4` is 512 words deep where the tile's switch matrix
// carries ten address wires, so ADDR[9] reaches no macro pin. The 1024-deep
// part of the same width would use it; the ECOS compiler has not generated one.
module ICS55_SRAM_512x32_1RW (
    // Fabric side
    input                 CLK,
    input  [(10 - 1) : 0] ADDR,
    input  [(32 - 1) : 0] DIN,
    input  [(32 - 1) : 0] BM,
    input                 WEN,
    input                 MEN,
    input                 REN,
    output [(32 - 1) : 0] DOUT,

    (* FABulous, EXTERNAL *) input CONFIGURED_top
);

    // Only enable the memory once the fabric is configured, since until then
    // the switch matrix drives MEN, WEN and BM from unwritten latches.
    wire enable = MEN && CONFIGURED_top;

    // `ics55_ecos_sram_512x32_m4_core.v` computes the write of bit n as
    // ~CEB & ~GWEB & ~WEB[n] and the read as ~CEB & GWEB, so the two enables
    // fold into one chip enable: writing needs WEN, reading needs REN and the
    // absence of WEN. What does not survive the fold is that a write updates Q
    // on the written bits whatever REN says, where the IHP part holds DOUT.
    wire ceb  = ~(enable && (WEN || REN));
    wire gweb = ~WEN;

    ics55_ecos_sram_512x32_m4 sram_inst (
        .CLK  (CLK),
        .CEB  (ceb),
        .GWEB (gweb),
        .WEB  (~BM),
        .A    (ADDR[8:0]),
        .D    (DIN),
        .Q    (DOUT),
        // MARE low takes the characterised read-margin setting, which is the
        // one every liberty corner in the package models. MAR is don't-care
        // there and only has to hold a level.
        .MAR  (4'b0000),
        .MARE (1'b0)
    );

endmodule
