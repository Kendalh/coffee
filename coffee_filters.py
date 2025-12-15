#!/usr/bin/env python3
"""
ENUM classes for coffee bean filters.
"""

from enum import Enum
from typing import Set


class CountryFilter(Enum):
    """Enumeration of coffee bean countries."""
    BRAZIL = "Brazil"
    COLOMBIA = "Colombia"
    ETHIOPIA = "埃塞俄比亚"  # Ethiopia
    GUATEMALA = "危地马拉"  # Guatemala
    KENYA = "肯尼亚"  # Kenya
    COSTA_RICA = "哥斯达黎加"  # Costa Rica
    PANAMA = "巴拿马"  # Panama
    INDONESIA = "印度尼西亚"  # Indonesia
    HONDURAS = "洪都拉斯"  # Honduras
    PERU = "秘鲁"  # Peru
    NICARAGUA = "尼加拉瓜"  # Nicaragua
    MEXICO = "墨西哥"  # Mexico
    TANZANIA = "坦桑尼亚"  # Tanzania
    RWANDA = "卢旺达"  # Rwanda
    UGANDA = "乌干达"  # Uganda
    EL_SALVADOR = "萨尔瓦多"  # El Salvador
    JAMAICA = "牙买加"  # Jamaica
    CHINA_YUNNAN = "云南"  # Yunnan, China
    LAOS = "老挝"  # Laos
    PAPUA_NEW_GUINEA = "巴布亚新几内亚"  # Papua New Guinea
    VIETNAM = "越南"  # Vietnam
    INDIA = "印度"  # India


class ProviderFilter(Enum):
    """Enumeration of coffee bean providers."""
    JIN_ZONG = "金粽"  # Jin Zong (from the CSV files)


class TypeFilter(Enum):
    """Enumeration of coffee bean types."""
    COMMON = "common"
    PREMIUM = "premium"


class VarietyFilter(Enum):
    """Enumeration of popular coffee bean varieties."""
    # Bourbon varieties
    BOURBON = "Bourbon"
    YELLOW_BOURBON = "Yellow Bourbon"
    ORANGE_BOURBON = "Orange Bourbon"
    RED_BOURBON = "Red Bourbon"
    PINK_BOURBON = "Pink Bourbon"
    
    # Caturra and related
    CATURRA = "Caturra"
    YELLOW_CATURRA = "Yellow Caturra"
    
    # Typica varieties
    TYPICA = "Typica"
    JAVA = "Java"
    
    # Geisha/Gesha varieties
    GEISHA = "Geisha"
    GESHA = "Gesha"
    GEISHA_1931 = "Geisha1931"
    GORI_GESHA = "Gori Gesha"
    
    # SL varieties
    SL28 = "SL28"
    SL34 = "SL34"
    
    # Heirloom (common for Ethiopian coffees)
    HEIRLOOM = "Heirloom"
    
    # Colombian varieties
    CASTILLO = "Castillo"
    CATORANO = "Catorano"
    
    # Processing specific
    CATIMOR = "Catimor"
    MANDING = "Manding"
    
    # Other notable varieties
    PACAMARA = "Pacamara"
    MARACATU = "Maracatu"
    SIDRA = "Sidra"
    VILLA_SARCHI = "Villa Sarchi"
    CARMELITO = "Carmelito"
    
    # Blue Mountain
    BLUE_MOUNTAIN = "BLUE MOUNTAIN"


def get_all_countries() -> Set[str]:
    """Return all country values as a set."""
    return {country.value for country in CountryFilter}


def get_all_providers() -> Set[str]:
    """Return all provider values as a set."""
    return {provider.value for provider in ProviderFilter}


def get_all_types() -> Set[str]:
    """Return all type values as a set."""
    return {type_filter.value for type_filter in TypeFilter}


def get_all_varieties() -> Set[str]:
    """Return all variety values as a set."""
    return {variety.value for variety in VarietyFilter}


if __name__ == "__main__":
    # Example usage
    print("Available Countries:")
    for country in CountryFilter:
        print(f"  {country.name}: {country.value}")
    
    print("\nAvailable Providers:")
    for provider in ProviderFilter:
        print(f"  {provider.name}: {provider.value}")
    
    print("\nAvailable Types:")
    for type_filter in TypeFilter:
        print(f"  {type_filter.name}: {type_filter.value}")
    
    print("\nAvailable Varieties:")
    for variety in VarietyFilter:
        print(f"  {variety.name}: {variety.value}")