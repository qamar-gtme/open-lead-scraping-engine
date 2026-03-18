from __future__ import annotations

from lists.base import ListTypeMeta, ListTypePlugin


class HighVolumeList(ListTypePlugin):
    meta = ListTypeMeta(
        key="high_volume",
        name="High Volume Support Teams",
        description="Companies likely handling high support ticket volumes.",
    )

    def get_anchors(self, regions: list[str]) -> list[str]:
        return [
            "https://www.booking.com",
            "https://www.bol.com",
            "https://www.zalando.com",
            "https://www.hellofresh.com",
            "https://www.ryanair.com",
        ]


PLUGIN = HighVolumeList()
