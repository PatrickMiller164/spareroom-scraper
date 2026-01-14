import src.utils.utils as ut
from src.utils.logger_config import logger
from typing import Any

class RoomNormaliser:
    def normalise(self, room_data: dict[str, Any]) -> dict[str, Any]:
        """Reformat, rename, and cast room_data dict"""
        room_data = self._reformat_keys(room_data)
        room_data = self._rename_keys(room_data)
        room_data = self._cast_keys(room_data)
        room_data = self._convert_to_bool(room_data)
        return room_data

    def _reformat_keys(self, room_data: dict) -> dict:
        """Rename room attributes"""
        prices, room_sizes, deposits = [], [], []

        for k, v in room_data.items():
            if k.startswith("£") and "(NOW LET)" not in v:
                size = "double" if "double" in v else "single"
                room_sizes.append(size)

                price = ut.string_to_number(k)
                if price is not None:
                    if "pw" in k.lower():
                        price = price * 52 / 12
                    prices.append(price)

            if "deposit" in k.lower():
                deposit = ut.string_to_number(v)
                if deposit is not None:
                    deposits.append(deposit)

        if prices:
            room_data['average_price'] = int(sum(prices) / len(prices))
        if room_sizes:
            room_data['room_sizes'] = room_sizes
        if deposits:
            room_data['average_deposit'] = sum(deposits) / len(deposits)

        return room_data

    def _rename_keys(self, room_data: dict) -> dict:
        """Rename keys from scraped field names to standard field names."""
        RENAMING = {
            '#_flatmates': 'number_of_flatmates',
            '#_housemates': 'number_of_flatmates',
            'bills_included?': 'bills_included',
            'total_#_rooms': 'total_number_of_rooms',
            'garden/patio': 'garden_or_patio',
            'balcony/roof_terrace': 'balcony_or_roof_terrace'
        }

        new = {RENAMING[k]: room_data.get(k) for k in room_data if k in RENAMING}

        room_data.update(new)
        return room_data

    def _cast_keys(self, room_data: dict) -> dict:
        """Cast certain fields to the appropriate types."""
        CASTS = {
            'number_of_flatmates': int,
            'total_number_of_rooms': int
        }

        for key, value in room_data.items():
            if key in CASTS and value is not None:
                try:
                    room_data[key] = CASTS[key](value)
                except (ValueError, TypeError):
                    logger.warning(f"Failed to cast {key}='{value}'")
        return room_data
    
    def _convert_to_bool(self, room_data: dict) -> dict:
        """Converts string values to bool equivalent"""
            # Get metrics from room dictionary
        metrics_to_convert = [
            'bills_included', 
            'broadband_included', 
            'furnishings', 
            'garden_or_patio', 
            'living_room', 
            'balcony_or_rooftop_terrace'
        ]
        GOOD_VALS = ['furnished', 'yes', 'shared', 'some']
        BAD_VALS = ['unfurnished', 'no']

        for k, v in room_data.items():
            if k not in metrics_to_convert:
                continue
            
            val = ut.clean_string(v) if isinstance(v, str) else None
            if val in GOOD_VALS:
                room_data[k] = True
            elif val in BAD_VALS:
                room_data[k] = False
            else:
                logger.warning(f"Found unexpected string '{val}' for {k}")

        return room_data