#!/usr/bin/env python3
"""
ENUM classes for coffee bean filters.
"""

from enum import Enum
from typing import Set
import json
import os


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


class FlavorCategoryFilter(Enum):
    """Enumeration of flavor categories."""
    BRIGHT_FRUITY_ACIDITY = "明亮果酸型"  # Bright & Fruity Acidity
    FLORAL_TEA_LIKE = "花香茶感型"  # Floral & Tea-like
    JUICY_TROPICAL_FRUIT = "果汁感热带水果型"  # Juicy & Tropical Fruit
    BALANCED_CLEAN = "均衡圆润型"  # Balanced & Clean
    CHOCOLATE_NUTTY = "巧克力坚果调型"  # Chocolate & Nutty
    CARAMEL_SWEETNESS = "焦糖甜感型"  # Caramel Sweetness
    WINEY_FERMENTED = "酒香发酵型"  # Winey & Fermented
    EARTHY_SPICY = "烟熏木质型"  # Earthy & Spicy
    UNCATEGORIZED = "未分类"  # Uncategorized


def get_all_countries() -> Set[str]:
    """Return all country values as a set."""
    return {country.value for country in CountryFilter}


def get_all_providers() -> Set[str]:
    """Return all provider values as a set."""
    return {provider.value for provider in ProviderFilter}


def get_all_types() -> Set[str]:
    """Return all type values as a set."""
    return {type_filter.value for type_filter in TypeFilter}


def get_all_flavor_categories() -> Set[str]:
    """Return all flavor category values as a set."""
    # Load flavor categories from JSON file
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_file_path = os.path.join(current_dir, 'flavor_cateogy.json')
        with open(json_file_path, 'r', encoding='utf-8') as f:
            flavor_data = json.load(f)
        
        # Extract flavor categories from JSON
        categories = {item['flavor_category'] for item in flavor_data}
        # Add the uncategorized option
        categories.add("未分类")
        return categories
    except Exception:
        # Fallback to enum values if JSON loading fails
        return {category.value for category in FlavorCategoryFilter}


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
    
    print("\nAvailable Flavor Categories:")
    for category in FlavorCategoryFilter:
        print(f"  {category.name}: {category.value}")
    