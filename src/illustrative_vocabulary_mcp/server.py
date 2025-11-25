"""
Illustrative Visual Vocabulary MCP Server

Three-layer architecture:
1. Intent Analysis (Claude) - Extract creative intent from user request
2. Deterministic Taxonomy (Pure lookup) - Map to locked visual parameters
3. Synthesis (Claude) - Weave parameters into coherent prompt

This server helps users maintain aesthetic consistency when generating
illustrative artwork by locking visual parameters to specific illustration
styles, preventing downstream style drift.
"""

import json
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP

# ============================================================================
# LAYER 2: DETERMINISTIC TAXONOMY - Pure lookup functions (zero LLM cost)
# ============================================================================

class IllustrationStyle(str, Enum):
    """Primary illustration styles with locked visual parameters."""
    COMIC_BOOK = "comic_book"
    CHILDREN_BOOK = "children_book"
    TECHNICAL = "technical"
    FASHION = "fashion"
    WATERCOLOR = "watercolor"
    CONCEPT_ART = "concept_art"


# Deterministic taxonomy - maps style to locked visual parameters
ILLUSTRATION_TAXONOMY = {
    "comic_book": {
        "style_name": "Comic Book / Graphic Novel",
        "edge_treatment": [
            "hard, defined outlines",
            "consistent line weight",
            "bold contours",
            "crisp edges"
        ],
        "color_strategy": [
            "limited palette of 8-12 colors",
            "high contrast",
            "flat color blocking (no gradients)",
            "bold primaries and secondaries"
        ],
        "texture_approach": [
            "solid, non-photorealistic surfaces",
            "no photorealism",
            "graphic simplification",
            "uniform fill areas"
        ],
        "lighting_model": [
            "dramatic lighting",
            "high contrast shadows",
            "defined shadow edges",
            "no soft ambient glow"
        ],
        "line_weight": [
            "consistent line weight",
            "expressive line work",
            "visible strokes",
            "no thin/delicate lines"
        ],
        "depth_handling": [
            "flat layering",
            "clear silhouettes",
            "no depth of field blur",
            "sharp focus throughout"
        ],
        "compositional_rules": [
            "strong compositional balance",
            "bold shapes dominate",
            "clear foreground/background",
            "dramatic diagonal compositions"
        ],
        "negative_prompt_elements": [
            "photorealism",
            "soft gradients",
            "depth of field blur",
            "ambient occlusion",
            "photographic texture",
            "fine detail",
            "watercolor wash",
            "pastel"
        ]
    },
    "children_book": {
        "style_name": "Children's Book Illustration",
        "edge_treatment": [
            "softer edges",
            "slightly rounded forms",
            "gentle line work",
            "some outline softness"
        ],
        "color_strategy": [
            "warm, inviting palette",
            "medium saturation",
            "accessible colors (not extreme contrast)",
            "playful, cheerful tones"
        ],
        "texture_approach": [
            "visible brushwork or marker quality",
            "organic texture",
            "hand-drawn feeling",
            "not smooth or digital-looking"
        ],
        "lighting_model": [
            "soft, warm lighting",
            "gentle highlights",
            "no harsh shadows",
            "ambient, approachable lighting"
        ],
        "line_weight": [
            "varied line weight for expressiveness",
            "visible hand-drawn strokes",
            "playful, loose linework",
            "warm and inviting"
        ],
        "depth_handling": [
            "readable depth but not extreme",
            "clear subjects",
            "soft focus backgrounds",
            "minimal depth of field effect"
        ],
        "compositional_rules": [
            "centered, balanced composition",
            "clear subject focus",
            "friendly negative space",
            "inviting arrangement"
        ],
        "negative_prompt_elements": [
            "photorealism",
            "harsh shadows",
            "extreme contrast",
            "dark moody lighting",
            "digital smooth texture",
            "precise geometric rendering",
            "adult aesthetic"
        ]
    },
    "technical": {
        "style_name": "Technical Illustration",
        "edge_treatment": [
            "precise, clean lines",
            "exact geometric edges",
            "mechanical precision",
            "technical accuracy"
        ],
        "color_strategy": [
            "muted, professional palette",
            "strategic color for emphasis",
            "grayscale with accent colors",
            "limited, functional colors"
        ],
        "texture_approach": [
            "smooth, clean rendering",
            "no organic randomness",
            "precise surface definition",
            "clinical accuracy"
        ],
        "lighting_model": [
            "even, consistent lighting",
            "clear visibility",
            "minimal atmospheric effects",
            "functional illumination"
        ],
        "line_weight": [
            "consistent, precise line weight",
            "technical rendering",
            "mechanical exactitude",
            "clean vector-like quality"
        ],
        "depth_handling": [
            "isometric or orthographic perspective",
            "clear depth indication",
            "cutaway views when needed",
            "anatomical/structural clarity"
        ],
        "compositional_rules": [
            "functional layout",
            "emphasis on clarity",
            "hierarchy of importance",
            "unambiguous representation"
        ],
        "negative_prompt_elements": [
            "artistic interpretation",
            "atmospheric effects",
            "painterly texture",
            "soft edges",
            "color grading",
            "cinematic lighting",
            "stylization"
        ]
    },
    "fashion": {
        "style_name": "Fashion Editorial Illustration",
        "edge_treatment": [
            "elegant, flowing lines",
            "expressive linework",
            "stylized contours",
            "fashion-forward simplification"
        ],
        "color_strategy": [
            "sophisticated palette",
            "often monochromatic or limited",
            "high-fashion color sensibility",
            "dramatic accent colors"
        ],
        "texture_approach": [
            "mixed texture approach",
            "graphic flatness with dramatic flourishes",
            "texture for fabric emphasis",
            "stylized not photorealistic"
        ],
        "lighting_model": [
            "dramatic, editorial lighting",
            "strong directional light",
            "theatrical illumination",
            "fashion photography-inspired but stylized"
        ],
        "line_weight": [
            "variable line weight for expression",
            "elegant, flowing strokes",
            "expressive but controlled",
            "fashion-illustration style"
        ],
        "depth_handling": [
            "figure-forward composition",
            "simplified backgrounds",
            "focus on silhouette",
            "dramatic foreshortening"
        ],
        "compositional_rules": [
            "elongated proportions",
            "dynamic pose emphasis",
            "fashion-forward framing",
            "editorial sensibility"
        ],
        "negative_prompt_elements": [
            "realistic proportions",
            "photorealism",
            "casual everyday aesthetic",
            "neutral presentation",
            "busy backgrounds",
            "anatomical accuracy over style"
        ]
    },
    "watercolor": {
        "style_name": "Watercolor Painting",
        "edge_treatment": [
            "soft, diffuse edges",
            "organic edge dissolution",
            "color bleeding",
            "watercolor wash effects"
        ],
        "color_strategy": [
            "transparent color layers",
            "luminous color mixing",
            "natural pigment appearance",
            "color glazing and transparency"
        ],
        "texture_approach": [
            "visible wet texture",
            "paper texture visible",
            "organic, flowing surfaces",
            "characteristic watercolor paper grain"
        ],
        "lighting_model": [
            "natural, atmospheric lighting",
            "warm, inviting illumination",
            "luminosity through transparency",
            "soft light diffusion"
        ],
        "line_weight": [
            "minimal or organic linework",
            "suggested forms",
            "flowing, gestural marks",
            "no hard outlines"
        ],
        "depth_handling": [
            "atmospheric perspective",
            "color temperature for depth",
            "gradual value transitions",
            "soft focus on backgrounds"
        ],
        "compositional_rules": [
            "loose, suggestive composition",
            "balance through color wash",
            "negative space is white paper",
            "improvisational feel"
        ],
        "negative_prompt_elements": [
            "hard edges",
            "graphic flattening",
            "digital smoothness",
            "heavy definition",
            "opaque coverage",
            "precise geometric forms",
            "vector graphics"
        ]
    },
    "concept_art": {
        "style_name": "Concept Art / Painting",
        "edge_treatment": [
            "varied edge treatment",
            "soft atmospheric edges",
            "hard edges for emphasis",
            "dynamic edge variation"
        ],
        "color_strategy": [
            "rich, saturated colors",
            "color harmony and balance",
            "atmospheric color shifts",
            "cinematic color grading"
        ],
        "texture_approach": [
            "painterly texture visible",
            "brushwork emphasis",
            "varied surface texture",
            "tactile paint application"
        ],
        "lighting_model": [
            "cinematic lighting",
            "dramatic chiaroscuro",
            "atmospheric effects",
            "volumetric lighting"
        ],
        "line_weight": [
            "varied linework",
            "painterly no-line approach",
            "form emphasis through value",
            "expressive mark-making"
        ],
        "depth_handling": [
            "atmospheric perspective",
            "volumetric depth",
            "soft background focus",
            "dramatic foreground/background separation"
        ],
        "compositional_rules": [
            "cinematic composition",
            "rule of thirds application",
            "dramatic diagonal lines",
            "environmental storytelling"
        ],
        "negative_prompt_elements": [
            "clean digital render",
            "graphic flatness",
            "technical precision",
            "photorealism",
            "vector graphics",
            "smooth gradients",
            "minimal composition"
        ]
    }
}


def get_style_parameters(style: str) -> Dict[str, Any]:
    """
    LAYER 2: Deterministic taxonomy lookup.
    Returns locked visual parameters for specified illustration style.
    
    This is pure deterministic mapping - no LLM involved.
    """
    style_lower = style.lower().replace(" ", "_").replace("_book", "_book")
    
    if style_lower in ILLUSTRATION_TAXONOMY:
        return ILLUSTRATION_TAXONOMY[style_lower]
    
    # Try to match by style name
    for key, params in ILLUSTRATION_TAXONOMY.items():
        if style.lower() in params["style_name"].lower():
            return params
    
    raise ValueError(
        f"Style '{style}' not found. Available styles: "
        f"{', '.join([s.value for s in IllustrationStyle])}"
    )


def format_parameters_as_prompt_elements(params: Dict[str, Any]) -> str:
    """Convert locked parameters to prompt-friendly text elements."""
    elements = []
    
    for category, items in params.items():
        if category == "style_name":
            continue
        if isinstance(items, list):
            elements.append(", ".join(items))
    
    return ". ".join(elements) + "."


# ============================================================================
# LAYER 1: INTENT ANALYSIS - Pydantic models for input validation
# ============================================================================

class IntentAnalysisInput(BaseModel):
    """Parse user's creative intent for illustrative work."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    user_prompt: str = Field(
        ...,
        description="User's request for illustrative artwork (e.g., 'I want a comic book style scene of a cyberpunk street')",
        min_length=10,
        max_length=1000
    )
    
    illustration_style: str = Field(
        ...,
        description="Target illustration style: comic_book, children_book, technical, fashion, watercolor, or concept_art",
        min_length=3,
        max_length=50
    )


class ParameterOverrideInput(BaseModel):
    """Allow users to override specific parameters from the taxonomy."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    illustration_style: str = Field(
        ...,
        description="Base illustration style to start from",
        min_length=3,
        max_length=50
    )
    
    override_color_strategy: Optional[List[str]] = Field(
        default=None,
        description="Override default color approach (list of color strategy descriptions)",
        max_length=5
    )
    
    override_lighting: Optional[List[str]] = Field(
        default=None,
        description="Override default lighting model (list of lighting descriptions)",
        max_length=5
    )
    
    override_edges: Optional[List[str]] = Field(
        default=None,
        description="Override default edge treatment (list of edge descriptions)",
        max_length=5
    )


class StyleComparisonInput(BaseModel):
    """Compare visual parameters between two illustration styles."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    style1: str = Field(..., description="First illustration style to compare", min_length=3, max_length=50)
    style2: str = Field(..., description="Second illustration style to compare", min_length=3, max_length=50)


# ============================================================================
# MCP SERVER INITIALIZATION
# ============================================================================

mcp = FastMCP("illustrative_vocabulary_mcp")


# ============================================================================
# LAYER 2: DETERMINISTIC TOOLS (Pure taxonomy operations)
# ============================================================================

@mcp.tool(
    name="get_style_taxonomy",
    annotations={
        "title": "Get Illustration Style Taxonomy",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def get_style_taxonomy(params: IntentAnalysisInput) -> str:
    """
    Retrieve locked visual parameters for a specific illustration style.
    
    This is LAYER 2 - pure deterministic taxonomy lookup with zero LLM cost.
    Returns all visual parameters that prevent style drift for the chosen style.
    
    Args:
        params (IntentAnalysisInput): User request and target style
    
    Returns:
        str: JSON with locked visual parameters for the illustration style
    """
    try:
        style_params = get_style_parameters(params.illustration_style)
        
        result = {
            "style": style_params["style_name"],
            "locked_parameters": {
                "edge_treatment": style_params["edge_treatment"],
                "color_strategy": style_params["color_strategy"],
                "texture_approach": style_params["texture_approach"],
                "lighting_model": style_params["lighting_model"],
                "line_weight": style_params["line_weight"],
                "depth_handling": style_params["depth_handling"],
                "compositional_rules": style_params["compositional_rules"],
            },
            "negative_prompt_elements": style_params["negative_prompt_elements"],
            "prompt_synthesis_hint": (
                "These locked parameters should be preserved in final prompt. "
                "If any conflict with subject matter, prioritize these style parameters "
                "to maintain aesthetic consistency."
            )
        }
        
        return json.dumps(result, indent=2)
    
    except ValueError as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool(
    name="list_available_styles",
    annotations={
        "title": "List Available Illustration Styles",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def list_available_styles() -> str:
    """
    List all available illustration styles with brief descriptions.
    
    LAYER 2 - Pure taxonomy enumeration with zero LLM cost.
    
    Returns:
        str: JSON with all available illustration styles and their characteristics
    """
    styles = []
    for key, params in ILLUSTRATION_TAXONOMY.items():
        styles.append({
            "id": key,
            "name": params["style_name"],
            "key_characteristics": [
                ", ".join(params["edge_treatment"][:2]),
                ", ".join(params["color_strategy"][:2]),
                ", ".join(params["texture_approach"][:1])
            ]
        })
    
    return json.dumps({"available_styles": styles}, indent=2)


@mcp.tool(
    name="compare_styles",
    annotations={
        "title": "Compare Two Illustration Styles",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def compare_styles(params: StyleComparisonInput) -> str:
    """
    Compare visual parameters between two illustration styles.
    
    LAYER 2 - Pure deterministic comparison, no LLM cost.
    Useful for understanding differences and preventing unintended style drift.
    
    Args:
        params (StyleComparisonInput): Two styles to compare
    
    Returns:
        str: JSON with side-by-side parameter comparison
    """
    try:
        style1_params = get_style_parameters(params.style1)
        style2_params = get_style_parameters(params.style2)
        
        comparison = {
            "style_1": style1_params["style_name"],
            "style_2": style2_params["style_name"],
            "comparison": {
                "edge_treatment": {
                    "style_1": style1_params["edge_treatment"][:2],
                    "style_2": style2_params["edge_treatment"][:2]
                },
                "color_strategy": {
                    "style_1": style1_params["color_strategy"][:2],
                    "style_2": style2_params["color_strategy"][:2]
                },
                "lighting_model": {
                    "style_1": style1_params["lighting_model"][:2],
                    "style_2": style2_params["lighting_model"][:2]
                },
                "texture_approach": {
                    "style_1": style1_params["texture_approach"][:2],
                    "style_2": style2_params["texture_approach"][:2]
                }
            }
        }
        
        return json.dumps(comparison, indent=2)
    
    except ValueError as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool(
    name="override_parameters",
    annotations={
        "title": "Override Style Parameters",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def override_parameters(params: ParameterOverrideInput) -> str:
    """
    Create a custom parameter set by overriding specific aspects of a base style.
    
    LAYER 2 - Deterministic composition of taxonomy elements.
    Allows users to mix-and-match locked parameters while maintaining consistency.
    
    Args:
        params (ParameterOverrideInput): Base style and specific overrides
    
    Returns:
        str: JSON with modified parameter set
    """
    try:
        base_params = get_style_parameters(params.illustration_style)
        
        # Apply overrides
        result = base_params.copy()
        
        if params.override_color_strategy:
            result["color_strategy"] = params.override_color_strategy
        
        if params.override_lighting:
            result["lighting_model"] = params.override_lighting
        
        if params.override_edges:
            result["edge_treatment"] = params.override_edges
        
        custom_set = {
            "base_style": base_params["style_name"],
            "customized_parameters": {
                "edge_treatment": result["edge_treatment"],
                "color_strategy": result["color_strategy"],
                "texture_approach": result["texture_approach"],
                "lighting_model": result["lighting_model"],
                "line_weight": result["line_weight"],
                "depth_handling": result["depth_handling"],
                "compositional_rules": result["compositional_rules"],
            },
            "negative_prompt_elements": result["negative_prompt_elements"],
            "warning": "This custom set mixes parameters from different styles. "
                      "Verify compatibility before use."
        }
        
        return json.dumps(custom_set, indent=2)
    
    except ValueError as e:
        return json.dumps({"error": str(e)}, indent=2)


# ============================================================================
# INFORMATION & REFERENCE TOOLS
# ============================================================================

@mcp.tool(
    name="get_style_details",
    annotations={
        "title": "Get Detailed Style Information",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def get_style_details(params: IntentAnalysisInput) -> str:
    """
    Get comprehensive details about a specific illustration style.
    
    Includes all locked parameters, negative prompt elements, and usage guidance.
    
    Args:
        params (IntentAnalysisInput): Illustration style to detail
    
    Returns:
        str: JSON with complete style specification
    """
    try:
        style_params = get_style_parameters(params.illustration_style)
        
        details = {
            "style": style_params["style_name"],
            "complete_specification": style_params,
            "usage_guidance": (
                "These parameters are locked to prevent style drift. "
                "Include ALL of these descriptions in your final image generation prompt. "
                "They act as semantic anchors that override downstream style choices."
            )
        }
        
        return json.dumps(details, indent=2)
    
    except ValueError as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool(
    name="export_prompt_elements",
    annotations={
        "title": "Export Parameters as Prompt Elements",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def export_prompt_elements(params: IntentAnalysisInput) -> str:
    """
    Export locked parameters as prompt-friendly text elements.
    
    Returns a formatted string ready to embed in image generation prompts.
    These elements are locked to prevent the lighting/style drift Koray experienced.
    
    Args:
        params (IntentAnalysisInput): Illustration style to export
    
    Returns:
        str: Formatted prompt elements and negative prompt
    """
    try:
        style_params = get_style_parameters(params.illustration_style)
        
        positive_elements = format_parameters_as_prompt_elements(style_params)
        negative_elements = ", ".join(style_params["negative_prompt_elements"])
        
        export = {
            "style": style_params["style_name"],
            "positive_prompt_elements": positive_elements,
            "negative_prompt": f"NOT: {negative_elements}",
            "instruction": (
                "Copy both positive_prompt_elements and negative_prompt into your final prompt. "
                "The negative_prompt is critical - it explicitly prevents style drift by blocking "
                "incompatible aesthetics that would override your chosen illustration style."
            )
        }
        
        return json.dumps(export, indent=2)
    
    except ValueError as e:
        return json.dumps({"error": str(e)}, indent=2)


def main() -> None:
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
