import json


class Event(object):
    def __init__(self, name, data):
        self.Name = name
        self.Data = data


class AggregateRootEntity(object):
    def __init__(self):
        self.__changes = []
        self.__handlers = dict()

    def initialize(self, events):
        if len(self.__changes) > 0:
            raise RuntimeError("Initialize cannot be called on an instance with changes.")
        for event in events:
            self.__play(event)

    def has_changes(self):
        return len(self.__changes) > 0

    def get_changes(self):
        return self.__changes

    def clear_changes(self):
        del self.__changes[:]

    def _route(self, name, method):
        if name in self.__handlers:
            raise KeyError("'" + name + "' is already routed to a method.")
        self.__handlers[name] = method

    def _apply(self, event):
        self.__play(event)
        self.__record(event)

    def __play(self, event):
        if event.Name in self.__handlers:
            self.__handlers[event.Name](event.Data)

    def __record(self, event):
        self.__changes.append(event)


class Item(AggregateRootEntity):
    def __init__(self):
        AggregateRootEntity.__init__(self)
        self._route(ItemEventNames.InventoryItemCreated(), self.__when_inventory_item_created)
        self._route(ItemEventNames.ItemsCheckedInToInventory(), self.__when_items_checked_into_inventory)
        self._route(ItemEventNames.ItemsRemovedFromInventory(), self.__when_items_removed_from_inventory)
        self._route(ItemEventNames.InventoryItemDeactivated(), self.__when_inventory_item_deactivated)

    @classmethod
    def create_item(cls, id, name):
        instance = Item()
        instance.__create_item(id, name)
        return instance

    def __create_item(self, id, name):
        self._apply(ItemEvents.InventoryItemCreated(id, name))

    def change_name(self, new_name):
        if len(new_name) == 0:
            raise Exception("We need a name, not an empty piece of string.")
        self._apply(ItemEvents.InventoryItemRenamed(self.__id, new_name))

    def check_in(self, count):
        if count <= 0:
            raise Exception("Must have a count greater than 0 to add to the inventory.")
        self._apply(ItemEvents.ItemsCheckedInToInventory(self.__id, count))

    def remove(self, count):
        if count <= 0:
            raise Exception("Must have a count greater than 0 to remove from the inventory.")
        self._apply(ItemEvents.ItemsRemovedFromInventory(self.__id, count))

    def deactivate(self):
        if self.__deactivated:
            raise Exception("Already deactivated, moron!")
        self._apply(ItemEvents.InventoryItemDeactivated(self.__id))

    def __when_inventory_item_created(self, data):
        self.__id = data["Id"]
        self.__count = 0
        self.__deactivated = False

    def __when_items_checked_into_inventory(self, data):
        self.__count += data["Count"]

    def __when_items_removed_from_inventory(self, data):
        self.__count -= data["Count"]

    def __when_inventory_item_deactivated(self, data):
        self.__deactivated = True


class ItemEvents(object):
    @classmethod
    def InventoryItemDeactivated(cls, id):
        return Event(ItemEventNames.InventoryItemDeactivated(), dict({"Id": id}))

    @classmethod
    def InventoryItemCreated(cls, id, name):
        return Event(ItemEventNames.InventoryItemCreated(), dict({"Id": id, "Name": name}))

    @classmethod
    def InventoryItemRenamed(cls, id, new_name):
        return Event(ItemEventNames.InventoryItemRenamed(), dict({"Id": id, "NewName": new_name}))

    @classmethod
    def ItemsCheckedInToInventory(cls, id, count):
        return Event(ItemEventNames.ItemsCheckedInToInventory(), dict({"Id": id, "Count": count}))

    @classmethod
    def ItemsRemovedFromInventory(cls, id, count):
        return Event(ItemEventNames.ItemsRemovedFromInventory(), dict({"Id": id, "Count": count}))


class ItemEventNames(object):
    @classmethod
    def InventoryItemDeactivated(cls):
        return 'inventory-item-deactivated'

    @classmethod
    def InventoryItemCreated(cls):
        return 'inventory-item-created'

    @classmethod
    def InventoryItemRenamed(cls):
        return 'inventory-item-renamed'

    @classmethod
    def ItemsCheckedInToInventory(cls):
        return 'items-checked-into-inventory'

    @classmethod
    def ItemsRemovedFromInventory(cls):
        return 'items-removed-from-inventory'

item = Item.create_item(123, "iPad")
item.change_name("iPhone")
item.check_in(100)
item.remove(5)
item.deactivate()
for change in item.get_changes():
    print change.Name + " " + json.dumps(change.Data)
