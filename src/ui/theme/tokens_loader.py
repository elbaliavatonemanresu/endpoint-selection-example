"""Design tokens loader for CTTI theming."""
import json
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel


class TextColors(BaseModel):
    """Text color definitions."""

    primary: str
    secondary: str
    inverse: str


class ColorTokens(BaseModel):
    """Color token definitions."""

    primary: str
    secondary: str
    background: str
    surface: str
    accent: str
    error: str
    text: TextColors
    border: str


class FontSizes(BaseModel):
    """Font size definitions."""

    xl: str
    lg: str
    md: str
    sm: str
    xs: str


class FontWeights(BaseModel):
    """Font weight definitions."""

    bold: int
    semibold: int
    normal: int
    light: int


class FontTokens(BaseModel):
    """Font token definitions."""

    family: str
    size: FontSizes
    weight: FontWeights


class SpaceTokens(BaseModel):
    """Spacing token definitions."""

    xs: str
    sm: str
    md: str
    lg: str
    xl: str
    xxl: str


class BorderRadius(BaseModel):
    """Border radius definitions."""

    sm: str
    md: str


class BorderTokens(BaseModel):
    """Border token definitions."""

    radius: BorderRadius
    width: str
    color: str


class ElevationTokens(BaseModel):
    """Elevation (shadow) token definitions."""

    card: str
    modal: str


class DesignTokens(BaseModel):
    """Complete design token set."""

    color: ColorTokens
    font: FontTokens
    space: SpaceTokens
    border: BorderTokens
    elevation: ElevationTokens


class TokensLoader:
    """Loader for design tokens with caching."""

    _cache: Optional[DesignTokens] = None
    _cache_path: Optional[str] = None

    @classmethod
    def load(cls, tokens_path: Optional[str] = None) -> DesignTokens:
        """
        Load design tokens from JSON file.

        Args:
            tokens_path: Optional path to tokens JSON file.
                        Defaults to assets/tokens/ctti.tokens.json

        Returns:
            Loaded design tokens

        Raises:
            FileNotFoundError: If tokens file doesn't exist
            ValueError: If tokens file is invalid
        """
        if tokens_path is None:
            # Default path
            tokens_path = str(
                Path(__file__).parent.parent.parent.parent
                / "assets"
                / "tokens"
                / "ctti.tokens.json"
            )

        # Return cached tokens if loading same file
        if cls._cache is not None and cls._cache_path == tokens_path:
            return cls._cache

        # Load tokens file
        tokens_file = Path(tokens_path)
        if not tokens_file.exists():
            raise FileNotFoundError(f"Tokens file not found: {tokens_path}")

        try:
            with open(tokens_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            tokens = DesignTokens.model_validate(data)

            # Cache the loaded tokens
            cls._cache = tokens
            cls._cache_path = tokens_path

            return tokens

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in tokens file: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load tokens: {e}")

    @classmethod
    def clear_cache(cls):
        """Clear the tokens cache."""
        cls._cache = None
        cls._cache_path = None
