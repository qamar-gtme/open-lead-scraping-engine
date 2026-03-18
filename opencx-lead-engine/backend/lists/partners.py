from __future__ import annotations

from lists.base import ListTypeMeta, ListTypePlugin


class PartnersList(ListTypePlugin):
    meta = ListTypeMeta(
        key="partners",
        name="Partner Ecosystem Targets",
        description="Implementation partners and consultancies supporting support stacks.",
    )

    def get_anchors(self, regions: list[str]) -> list[str]:
        return [
            "https://www.accenture.com",
            "https://www.capgemini.com",
            "https://www.deptagency.com",
            "https://www.reply.com",
            "https://www.kinandcarta.com",
        ]

    def get_system_prompt(self) -> str:
        return (
            super().get_system_prompt()
            + "\nPrioritize partner, reseller, implementation, and consulting signals."
        )


PLUGIN = PartnersList()
