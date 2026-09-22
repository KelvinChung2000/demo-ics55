# The ECOS Factory views of `ics55_ecos_sram_512x32_m4`

Two files out of the release package, the ones the ECC flow reads. The abstract
LEF gives the floorplanner the 164.430 x 90.535 um outline, the MET1 to MET3
signal pins and the MET4 power pins; `ss1p08v125ccmax` is the corner the ICS55
standard cells are characterised at in this flow, so it is the one every step
after synthesis times against.

The other seven corners, the behavioural and stub Verilog, the CPF and the
datasheet stay out of the repository and come from the package:

    https://github.com/openecos-projects/ics55_ecos_sram/releases/download/sram-v1-71fed9dcc70b55685ac777512f3face612c45b3a2fd66f64d0bc97349276d5cc/ics55_ecos_sram_512x32_m4.tar.gz

The package ships no GDS, so a tile built against these views is an abstract
with a hole where the macro sits. It abuts, stitches and views; it is not
LVS-complete until OpenECOS publishes the layout.
