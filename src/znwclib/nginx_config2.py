from typing import Union


class Location:
    def __init__(self, location: Union[str, tuple], block: list):
        self.location = location if isinstance(location, str) else ''.join(location)
        self.block = block
        self.subLocations = {}

    @property
    def locations(self) -> dict:
        """
        :return: list of all locations include sub locations or empty list
        """
        return self.subLocations
