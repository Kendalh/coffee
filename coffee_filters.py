#!/usr/bin/env python3
"""
ENUM classes for coffee bean filters.
"""

from enum import Enum
from typing import Set


class CountryFilter(Enum):
    """Enumeration of coffee bean countries."""
    BRAZIL = "巴西"
    COLOMBIA = "哥伦比亚"
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
    CHINA_YUNNAN = "中国"  # Yunnan, China
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


def get_all_countries() -> Set[str]:
    """Return all country values as a set."""
    return {country.value for country in CountryFilter}


def get_all_providers() -> Set[str]:
    """Return all provider values as a set."""
    return {provider.value for provider in ProviderFilter}


def get_all_types() -> Set[str]:
    """Return all type values as a set."""
    return {type_filter.value for type_filter in TypeFilter}


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
    