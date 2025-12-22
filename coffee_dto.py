#!/usr/bin/env python3
"""
DTO classes for coffee bean data.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class CoffeeBeanDTO:
    """Data Transfer Object for coffee bean data."""
    name: str
    type: str
    country: str
    flavor_profile: str
    flavor_category: str
    origin: str
    harvest_season: int
    code: str
    price_per_kg: Optional[float]
    price_per_pkg: Optional[float]
    sold_out: bool
    grade: str
    altitude: str
    density: str
    processing_method: str
    variety: str
    humidity: str
    plot: str
    estate: str
    provider: str
    data_year: int
    data_month: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CoffeeBeanDTO':
        """Create a CoffeeBeanDTO from a dictionary."""
        return cls(
            name=data.get('name', ''),
            type=data.get('type', ''),
            country=data.get('country', ''),
            flavor_profile=data.get('flavor_profile', ''),
            flavor_category=data.get('flavor_category', ''),
            origin=data.get('origin', ''),
            harvest_season=data.get('harvest_season', 0),
            code=data.get('code', ''),
            price_per_kg=float(data['price_per_kg']) if data.get('price_per_kg') and data['price_per_kg'] != '' else None,
            price_per_pkg=float(data['price_per_pkg']) if data.get('price_per_pkg') and data['price_per_pkg'] != '' else None,
            sold_out=CoffeeBeanDTO._parse_boolean(data.get('sold_out', False)),
            grade=data.get('grade', ''),
            altitude=data.get('altitude', ''),
            density=data.get('density', ''),
            processing_method=data.get('processing_method', ''),
            variety=data.get('variety', ''),
            humidity=data.get('humidity', ''),
            plot=data.get('plot', ''),
            estate=data.get('estate', ''),
            provider=data.get('provider', ''),
            data_year=data.get('data_year', 0),
            data_month=data.get('data_month', 0)
        )

    @staticmethod
    def _parse_boolean(value) -> bool:
        """Parse various boolean representations to a proper boolean value."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lower_value = value.lower()
            if lower_value in ('true', '1', 'yes', 'on'):
                return True
            if lower_value in ('false', '0', 'no', 'off', ''):
                return False
        if isinstance(value, (int, float)):
            return bool(value)
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the CoffeeBeanDTO to a dictionary."""
        return {
            'name': self.name,
            'type': self.type,
            'country': self.country,
            'flavor_profile': self.flavor_profile,
            'flavor_category': self.flavor_category,
            'origin': self.origin,
            'harvest_season': self.harvest_season,
            'code': self.code,
            'price_per_kg': self.price_per_kg,
            'price_per_pkg': self.price_per_pkg,
            'sold_out': self.sold_out,
            'grade': self.grade,
            'altitude': self.altitude,
            'density': self.density,
            'processing_method': self.processing_method,
            'variety': self.variety,
            'humidity': self.humidity,
            'plot': self.plot,
            'estate': self.estate,
            'provider': self.provider,
            'data_year': self.data_year,
            'data_month': self.data_month
        }