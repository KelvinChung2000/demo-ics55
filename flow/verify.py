"""Check a plan against the fabric it was built from, before anything is run.

Four properties have to hold for an abutted fabric to be wired, and all four are
cheap to test on the plan alone. Testing them here rather than after fifteen
hardening runs is the difference between a second and an afternoon, and three of
the four were violated at some point while this flow was being written.
"""

from __future__ import annotations

from flow.fabric import Fabric
from flow.plan import Plan, stripe_keepout


def _origins(fabric: Fabric, plan: Plan) -> dict[tuple[int, int], object]:
    """Map every grid position a tile covers to the placement of that tile."""
    origins = {}
    for placement in plan.placements:
        for offset in range(fabric.tile_types[placement.tile_type].rows):
            origins[placement.column, placement.row + offset] = placement
    return origins


def check_plan(fabric: Fabric, plan: Plan) -> list[str]:
    """Return one line per property the plan fails, and an empty list when it holds."""
    failures = []

    duplicates = sum(
        len(offsets) - len(set(offsets))
        for pins in plan.pins.values()
        for side in "NESW"
        for offsets in [[pin.offset for pin in pins if pin.side == side]]
    )
    if duplicates:
        failures.append(f"{duplicates} pins share an offset with another pin on the same edge")

    origins = _origins(fabric, plan)
    lookup = {name: plan.pins_of(name) for name in plan.pins}
    misaligned = 0
    for link in fabric.links:
        driver, receiver = origins[link.driver_at], origins[link.receiver_at]
        near = lookup[driver.tile_type][link.driver.name]
        far = lookup[receiver.tile_type][link.receiver.name]
        if link.vertical_seam:
            misaligned += driver.y + near.offset != receiver.y + far.offset
        else:
            misaligned += driver.x + near.offset != receiver.x + far.offset
    if misaligned:
        failures.append(f"{misaligned} of {len(fabric.links)} links do not meet at one coordinate")

    under = sum(
        1
        for name, pins in plan.pins.items()
        for pin in pins
        if pin.side in "NS"
        and any(
            low <= pin.offset <= high
            for low, high in stripe_keepout(plan.tile_size[name][0], plan.stripe_pitch)
        )
    )
    if under:
        failures.append(f"{under} north or south pins sit under a MET4 power stripe")

    off = [
        f"{name}.{pin.name}"
        for name, pins in plan.pins.items()
        for pin in pins
        if pin.offset >= plan.tile_size[name][1 if pin.side in "EW" else 0]
    ]
    if off:
        failures.append(f"{len(off)} pins sit past the end of their edge: {off[:3]}")

    return failures
