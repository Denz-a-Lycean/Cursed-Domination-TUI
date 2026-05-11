"""Inventory container used by the player and combat item menu."""


class Inventory:
    """
    Handles player items.
    """

    def __init__(self):
        # Items stay in insertion order so rewards appear predictably in menus.
        self._items = []

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, value):
        self._items = list(value)

    def add_item(self, item):
        """Append a new item and return a message for the caller to display."""
        self._items.append(item)
        return f"Added item: {item.name}"

    def replace_items(self, items):
        """Swap the entire inventory, mainly when restoring checkpoints/saves."""
        self._items = list(items)

    def grouped_entries(self):
        """Group duplicate items so the combat inventory menu stays compact."""
        grouped = []
        entry_by_key = {}

        for index, item in enumerate(self._items):
            key = item.__class__.__name__
            if key not in entry_by_key:
                entry = {
                    "key": key,
                    "name": item.name,
                    "count": 0,
                    "indexes": [],
                }
                entry_by_key[key] = entry
                grouped.append(entry)

            entry = entry_by_key[key]
            entry["count"] += 1
            entry["indexes"].append(index)

        for entry in grouped:
            entry["label"] = (
                f"{entry['name']} x{entry['count']}"
                if entry["count"] > 1
                else entry["name"]
            )

        return grouped

    def use_item(self, index, player):
        """Try to use one raw item slot and consume it only on success."""
        if index < 0 or index >= len(self._items):
            return None

        item = self._items[index]
        result = item.apply(player)
        if result and result.get("success"):
            self._items.pop(index)
        return result

    def use_grouped_item(self, grouped_index, player):
        """Use one item from a grouped menu entry such as 'Potion x2'."""
        grouped = self.grouped_entries()
        if grouped_index < 0 or grouped_index >= len(grouped):
            return None

        item_index = grouped[grouped_index]["indexes"][0]
        return self.use_item(item_index, player)

    def is_empty(self):
        """Return True when the player has no usable items left."""
        return len(self._items) == 0

    def __len__(self):
        return len(self._items)

    def __getitem__(self, index):
        return self._items[index]

    def __str__(self):
        """Summarize the inventory contents for logs and debugging."""
        if not self._items:
            return "Inventory(empty)"
        grouped = ", ".join(entry["label"] for entry in self.grouped_entries())
        return f"Inventory({grouped})"
