from __future__ import annotations

from lists.base import ListTypeMeta, ListTypePlugin


class BPOList(ListTypePlugin):
    meta = ListTypeMeta(
        key="bpos",
        name="BPO / Outsourced Support",
        description="Business process outsourcers and CX outsourcing providers.",
    )

    def get_anchors(self, regions: list[str]) -> list[str]:
        return [
            "https://www.teleperformance.com",
            "https://www.concentrix.com",
            "https://www.foundever.com",
            "https://www.webhelp.com",
            "https://www.ttec.com",
        ]

    def get_system_prompt(self) -> str:
        return (
            super().get_system_prompt()
            + "\nPrioritize outsourced support operations, multilingual teams, and contact centers."
        )


PLUGIN = BPOList()
