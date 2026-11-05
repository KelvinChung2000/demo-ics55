"""cocotb testbench: each configuration port delivers the bitstream words in order."""

from collections.abc import Iterator
from enum import Enum, auto
from pathlib import Path
from typing import Protocol

import cocotb
from cocotb.clock import Clock
from cocotb.handle import LogicObject, LogicArrayObject
from cocotb.triggers import ClockCycles, RisingEdge, Timer

BITSTREAM = Path(__file__).parents[1] / "bitstream" / "sequential_16bit_en.bin"
# FABulous prepends the UART sync header and command 0x01 (binary mode) as word 0.
UART_HEADER_WORD = 0x00AAFF01

CLK_NS = 40.0  # 25 MHz
COM_RATE = 15
# config_UART ticks every ComRate + 1 cycles, not ComRate.
UART_BIT_NS = (COM_RATE + 1) * CLK_NS
# 0.4 ns past an integer ratio so the serial edges sweep every phase of CLK.
SPI_HALF_NS = 2 * CLK_NS + 0.4  # f_clk / f_sck = 4.02, just above the documented 4
BITBANG_QUARTER_NS = 2 * CLK_NS + 0.4
SPI_BURST_WORDS = 13  # one frame (header + 12 data) per CS assertion

BITBANG_ON = 0xFAB1
BITBANG_OFF = 0xFAB0


class Port(Enum):
    UART = auto()
    BITBANG = auto()
    SPI = auto()
    SELFWRITE = auto()


class FrontendDut(Protocol):
    CLK: LogicObject
    resetn: LogicObject
    Rx: LogicObject
    s_clk: LogicObject
    s_data: LogicObject
    spi_sck: LogicObject
    spi_cs_n: LogicObject
    spi_mosi: LogicObject
    SelfWriteData: LogicArrayObject
    SelfWriteStrobe: LogicObject
    bitstream_data: LogicArrayObject
    bitstream_valid: LogicObject


def read_words() -> list[int]:
    raw = BITSTREAM.read_bytes()
    assert len(raw) % 4 == 0, f"{BITSTREAM} is not whole 32-bit words"
    return [
        int.from_bytes(raw[i : i + 4], byteorder="big") for i in range(0, len(raw), 4)
    ]


def msb_first(word: int) -> Iterator[int]:
    return ((word >> i) & 1 for i in range(31, -1, -1))


async def reset(dut: FrontendDut) -> None:
    Clock(dut.CLK, CLK_NS, "ns").start()
    dut.resetn.value = 0
    dut.Rx.value = 1
    dut.s_clk.value = 0
    dut.s_data.value = 0
    dut.spi_sck.value = 0
    dut.spi_cs_n.value = 1
    dut.spi_mosi.value = 0
    dut.SelfWriteData.value = 0
    dut.SelfWriteStrobe.value = 0
    await ClockCycles(dut.CLK, 4)
    dut.resetn.value = 1
    await ClockCycles(dut.CLK, 4)


async def collect(dut: FrontendDut, received: list[int]) -> None:
    """Record bitstream_data on every CLK edge where bitstream_valid is high."""
    while True:
        # Values read straight after the edge are the ones fabric_config samples.
        if dut.bitstream_valid.value == 0:
            await RisingEdge(dut.bitstream_valid)
        await RisingEdge(dut.CLK)
        if dut.bitstream_valid.value == 1:
            received.append(dut.bitstream_data.value.to_unsigned())


async def send_uart(dut: FrontendDut, words: list[int]) -> None:
    for byte in b"".join(w.to_bytes(4, byteorder="big") for w in words):
        # start bit, 8 data bits LSB first, stop bit
        for bit in (0, *((byte >> i) & 1 for i in range(8)), 1):
            dut.Rx.value = bit
            await Timer(UART_BIT_NS, "ns")


async def send_bitbang_word(dut: FrontendDut, data: int, control: int) -> None:
    # Data is taken on s_clk rising edges, control on falling edges.
    for data_bit, control_bit in zip(msb_first(data), msb_first(control), strict=True):
        dut.s_data.value = data_bit
        await Timer(BITBANG_QUARTER_NS, "ns")
        dut.s_clk.value = 1
        await Timer(BITBANG_QUARTER_NS, "ns")
        dut.s_data.value = control_bit
        await Timer(BITBANG_QUARTER_NS, "ns")
        dut.s_clk.value = 0
        await Timer(BITBANG_QUARTER_NS, "ns")


async def send_bitbang(dut: FrontendDut, words: list[int]) -> None:
    for word in words:
        await send_bitbang_word(dut, data=word, control=BITBANG_ON)
    await send_bitbang_word(dut, data=0, control=BITBANG_OFF)


async def send_spi_bits(dut: FrontendDut, bits: Iterator[int]) -> None:
    for bit in bits:
        dut.spi_mosi.value = bit
        await Timer(SPI_HALF_NS, "ns")
        dut.spi_sck.value = 1
        await Timer(SPI_HALF_NS, "ns")
        dut.spi_sck.value = 0


async def send_spi(dut: FrontendDut, words: list[int]) -> None:
    # A 7-bit fragment cut short by CS must not produce a word.
    dut.spi_cs_n.value = 0
    await Timer(SPI_HALF_NS, "ns")
    await send_spi_bits(dut, iter([1] * 7))
    dut.spi_cs_n.value = 1
    await Timer(SPI_HALF_NS, "ns")
    for start in range(0, len(words), SPI_BURST_WORDS):
        dut.spi_cs_n.value = 0
        await Timer(SPI_HALF_NS, "ns")
        for word in words[start : start + SPI_BURST_WORDS]:
            await send_spi_bits(dut, msb_first(word))
        # CS rises with the last SCK fall, the earliest mode 0 allows.
        dut.spi_cs_n.value = 1
        await Timer(SPI_HALF_NS, "ns")


async def send_selfwrite(dut: FrontendDut, words: list[int]) -> None:
    # Back to back: fabric_config accepts a word every cycle.
    await RisingEdge(dut.CLK)
    for word in words:
        dut.SelfWriteData.value = word
        dut.SelfWriteStrobe.value = 1
        await RisingEdge(dut.CLK)
    dut.SelfWriteStrobe.value = 0


@cocotb.test(timeout_time=200, timeout_unit="ms")
@cocotb.parametrize(port=list(Port))
async def test_stream(dut: FrontendDut, port: Port) -> None:
    words = read_words()
    assert words[0] == UART_HEADER_WORD, (
        f"word 0 is {words[0]:#010x}, not the UART header"
    )
    await reset(dut)
    received: list[int] = []
    cocotb.start_soon(collect(dut, received))

    match port:
        case Port.UART:
            await send_uart(dut, words)
            expected = words[1:]
        case Port.BITBANG:
            await send_bitbang(dut, words)
            expected = words
        case Port.SPI:
            await send_spi(dut, words)
            expected = words
        case Port.SELFWRITE:
            await send_selfwrite(dut, words)
            expected = words
    await ClockCycles(dut.CLK, 16)

    assert len(received) == len(expected), (
        f"{len(received)} words out, {len(expected)} in"
    )
    mismatch = next(
        (i for i, (r, e) in enumerate(zip(received, expected)) if r != e), None
    )
    assert mismatch is None, (
        f"word {mismatch}: got {received[mismatch]:#010x}, expected {expected[mismatch]:#010x}"
    )
