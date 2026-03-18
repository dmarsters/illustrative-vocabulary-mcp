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
import math
from fastmcp import FastMCP

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


# ============================================================================
# LAYER 2: DETERMINISTIC TAXONOMY - Pure lookup functions (zero LLM cost)
# ============================================================================

# ──────────────────────────────────────────────────────────────────────────────
# PHASE 2.6 / 2.7: 5D NORMALIZED MORPHOSPACE
# ──────────────────────────────────────────────────────────────────────────────
#
# The illustrative vocabulary domain is projected into a 5-dimensional
# normalized parameter space [0, 1]^5 derived from the existing taxonomy axes:
#
#   edge_definition    – 0 = soft/diffuse        → 1 = hard/precise
#   color_richness     – 0 = monochrome/limited  → 1 = rich/saturated
#   texture_organicity – 0 = smooth/digital      → 1 = organic/painterly
#   lighting_drama     – 0 = even/functional     → 1 = dramatic/cinematic
#   depth_atmosphere   – 0 = flat/isometric      → 1 = atmospheric/volumetric
#
# Each canonical illustration style is anchored at ethnomathematically and
# aesthetically meaningful positions in this space.
# ──────────────────────────────────────────────────────────────────────────────

ILLUSTRATIVE_PARAMETER_NAMES = [
    "edge_definition",
    "color_richness",
    "texture_organicity",
    "lighting_drama",
    "depth_atmosphere",
]

# Canonical state coordinates in normalized 5D morphospace
ILLUSTRATIVE_COORDS = {
    "comic_book": {
        "edge_definition": 0.95,
        "color_richness": 0.45,
        "texture_organicity": 0.15,
        "lighting_drama": 0.80,
        "depth_atmosphere": 0.10,
    },
    "children_book": {
        "edge_definition": 0.35,
        "color_richness": 0.60,
        "texture_organicity": 0.70,
        "lighting_drama": 0.25,
        "depth_atmosphere": 0.40,
    },
    "technical": {
        "edge_definition": 1.00,
        "color_richness": 0.15,
        "texture_organicity": 0.05,
        "lighting_drama": 0.10,
        "depth_atmosphere": 0.20,
    },
    "fashion": {
        "edge_definition": 0.55,
        "color_richness": 0.50,
        "texture_organicity": 0.45,
        "lighting_drama": 0.85,
        "depth_atmosphere": 0.30,
    },
    "watercolor": {
        "edge_definition": 0.05,
        "color_richness": 0.75,
        "texture_organicity": 0.95,
        "lighting_drama": 0.35,
        "depth_atmosphere": 0.80,
    },
    "concept_art": {
        "edge_definition": 0.50,
        "color_richness": 0.90,
        "texture_organicity": 0.85,
        "lighting_drama": 0.95,
        "depth_atmosphere": 0.90,
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# PHASE 2.7: VISUAL TYPE VOCABULARY
# ──────────────────────────────────────────────────────────────────────────────
#
# Each visual type is anchored at a canonical state and carries image-
# generation keywords.  Nearest-neighbour matching uses Euclidean distance
# in the normalised 5D space (weight cutoff ~0.15).

ILLUSTRATIVE_VISUAL_TYPES = {
    "bold_graphic": {
        "coords": {
            "edge_definition": 0.95,
            "color_richness": 0.45,
            "texture_organicity": 0.15,
            "lighting_drama": 0.80,
            "depth_atmosphere": 0.10,
        },
        "keywords": [
            "bold graphic illustration",
            "hard defined outlines",
            "flat color blocking with limited palette",
            "high contrast dramatic shadows",
            "crisp silhouette edges",
            "solid non-photorealistic surfaces",
            "strong compositional balance",
        ],
    },
    "gentle_storybook": {
        "coords": {
            "edge_definition": 0.35,
            "color_richness": 0.60,
            "texture_organicity": 0.70,
            "lighting_drama": 0.25,
            "depth_atmosphere": 0.40,
        },
        "keywords": [
            "gentle storybook illustration",
            "soft rounded forms with warm palette",
            "visible hand-drawn brushwork",
            "playful loose linework",
            "soft warm ambient lighting",
            "inviting approachable composition",
            "organic hand-crafted texture",
        ],
    },
    "precise_technical": {
        "coords": {
            "edge_definition": 1.00,
            "color_richness": 0.15,
            "texture_organicity": 0.05,
            "lighting_drama": 0.10,
            "depth_atmosphere": 0.20,
        },
        "keywords": [
            "precise technical illustration",
            "exact geometric edges with mechanical precision",
            "muted professional grayscale with accent color",
            "smooth clean clinical rendering",
            "even consistent functional illumination",
            "isometric orthographic perspective",
            "unambiguous structural clarity",
        ],
    },
    "editorial_glamour": {
        "coords": {
            "edge_definition": 0.55,
            "color_richness": 0.50,
            "texture_organicity": 0.45,
            "lighting_drama": 0.85,
            "depth_atmosphere": 0.30,
        },
        "keywords": [
            "fashion editorial illustration",
            "elegant flowing stylized contours",
            "sophisticated limited palette with dramatic accents",
            "strong directional theatrical illumination",
            "figure-forward silhouette composition",
            "mixed graphic flatness with dramatic flourishes",
            "elongated proportions with dynamic pose emphasis",
        ],
    },
    "wet_wash": {
        "coords": {
            "edge_definition": 0.05,
            "color_richness": 0.75,
            "texture_organicity": 0.95,
            "lighting_drama": 0.35,
            "depth_atmosphere": 0.80,
        },
        "keywords": [
            "watercolor wash illustration",
            "soft diffuse edges with organic color bleeding",
            "transparent luminous color layers",
            "visible wet-on-wet paper grain texture",
            "natural atmospheric soft light diffusion",
            "atmospheric perspective through color temperature",
            "loose suggestive improvised composition",
        ],
    },
    "cinematic_painting": {
        "coords": {
            "edge_definition": 0.50,
            "color_richness": 0.90,
            "texture_organicity": 0.85,
            "lighting_drama": 0.95,
            "depth_atmosphere": 0.90,
        },
        "keywords": [
            "cinematic concept painting",
            "rich saturated colors with atmospheric color grading",
            "painterly visible brushwork with tactile texture",
            "dramatic chiaroscuro with volumetric lighting",
            "deep atmospheric perspective with volumetric depth",
            "varied edge treatment from soft atmosphere to hard emphasis",
            "environmental storytelling with cinematic composition",
        ],
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# PHASE 2.6: RHYTHMIC PRESETS
# ──────────────────────────────────────────────────────────────────────────────
#
# Period strategy for cross-domain composition:
#   Overlaps existing periods: 15, 18, 20, 22  (sync with nuclear, catastrophe,
#       diatom, heraldic, microscopy)
#   Gap-fillers:  11 (fills 10-12), 14 (fills 12-15), 26 (fills 25-30)
#
# Periods: [11, 14, 15, 18, 20, 22, 26]

ILLUSTRATIVE_RHYTHMIC_PRESETS = {
    "edge_contrast_sweep": {
        "state_a": "technical",
        "state_b": "watercolor",
        "pattern": "sinusoidal",
        "num_cycles": 3,
        "steps_per_cycle": 22,
        "description": "Maximum edge definition contrast: precise hard lines dissolve into soft diffuse washes and reform. Period 22 synchronises with catastrophe and heraldic domains.",
    },
    "warmth_cycle": {
        "state_a": "children_book",
        "state_b": "fashion",
        "pattern": "sinusoidal",
        "num_cycles": 4,
        "steps_per_cycle": 18,
        "description": "Warm approachable storybook softness cycles into dramatic editorial glamour. Period 18 synchronises with nuclear and diatom domains.",
    },
    "painterly_pulse": {
        "state_a": "comic_book",
        "state_b": "concept_art",
        "pattern": "sinusoidal",
        "num_cycles": 5,
        "steps_per_cycle": 14,
        "description": "Flat graphic boldness pulses into rich cinematic painterliness. Period 14 fills the gap between 12 and 15 in the cross-domain period landscape.",
    },
    "atmosphere_drift": {
        "state_a": "technical",
        "state_b": "concept_art",
        "pattern": "triangular",
        "num_cycles": 2,
        "steps_per_cycle": 26,
        "description": "Flat isometric precision drifts into deep atmospheric volume with linear ramp. Period 26 fills the gap between 25 and 30.",
    },
    "medium_transition": {
        "state_a": "watercolor",
        "state_b": "comic_book",
        "pattern": "sinusoidal",
        "num_cycles": 3,
        "steps_per_cycle": 20,
        "description": "Organic wet-media looseness transitions to crisp graphic discipline. Period 20 synchronises with microscopy, catastrophe and diatom.",
    },
    "editorial_shift": {
        "state_a": "fashion",
        "state_b": "children_book",
        "pattern": "sinusoidal",
        "num_cycles": 4,
        "steps_per_cycle": 15,
        "description": "Dramatic editorial sophistication shifts to gentle storybook warmth. Period 15 synchronises with nuclear, catastrophe and diatom.",
    },
    "texture_oscillation": {
        "state_a": "technical",
        "state_b": "watercolor",
        "pattern": "square",
        "num_cycles": 5,
        "steps_per_cycle": 11,
        "description": "Hard toggle between clinical smooth surfaces and organic wet textures. Period 11 fills the gap between 10 and 12.",
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# PHASE 2.6 / 2.7: LAYER 2 DETERMINISTIC HELPER FUNCTIONS
# ──────────────────────────────────────────────────────────────────────────────

def _euclidean_distance_5d(a: dict, b: dict) -> float:
    """Euclidean distance between two points in normalised 5D parameter space."""
    return math.sqrt(sum(
        (a[p] - b[p]) ** 2 for p in ILLUSTRATIVE_PARAMETER_NAMES
    ))


def _find_nearest_visual_type(state: dict) -> dict:
    """
    Nearest-neighbour lookup in visual type vocabulary.
    Returns dict with nearest_type, distance, keywords.
    """
    best_type = None
    best_dist = float("inf")
    for vtype, vdata in ILLUSTRATIVE_VISUAL_TYPES.items():
        d = _euclidean_distance_5d(state, vdata["coords"])
        if d < best_dist:
            best_dist = d
            best_type = vtype
    return {
        "nearest_type": best_type,
        "distance": round(best_dist, 6),
        "keywords": ILLUSTRATIVE_VISUAL_TYPES[best_type]["keywords"],
    }


def _generate_oscillation(num_steps: int, num_cycles: float, pattern: str) -> list:
    """Generate oscillation pattern alpha values in [0, 1].  Pure-python fallback."""
    values = []
    for i in range(num_steps):
        t = 2 * math.pi * num_cycles * i / num_steps
        if pattern == "sinusoidal":
            values.append(0.5 * (1 + math.sin(t)))
        elif pattern == "triangular":
            t_norm = (t / (2 * math.pi)) % 1.0
            values.append(2 * t_norm if t_norm < 0.5 else 2 * (1 - t_norm))
        elif pattern == "square":
            t_norm = (t / (2 * math.pi)) % 1.0
            values.append(0.0 if t_norm < 0.5 else 1.0)
        else:
            raise ValueError(f"Unknown pattern: {pattern}")
    return values


def _interpolate_states(state_a: dict, state_b: dict, alpha: float) -> dict:
    """Linear interpolation between two canonical states."""
    return {
        p: state_a[p] * (1.0 - alpha) + state_b[p] * alpha
        for p in ILLUSTRATIVE_PARAMETER_NAMES
    }


def _generate_preset_trajectory(preset_name: str) -> list:
    """
    Generate full Phase 2.6 preset trajectory as list of 5D state dicts.
    Uses forced orbit integration: np.linspace over full cycle count,
    guaranteeing periodic closure with zero drift.
    """
    preset = ILLUSTRATIVE_RHYTHMIC_PRESETS[preset_name]
    state_a = ILLUSTRATIVE_COORDS[preset["state_a"]]
    state_b = ILLUSTRATIVE_COORDS[preset["state_b"]]
    total_steps = preset["num_cycles"] * preset["steps_per_cycle"]

    alphas = _generate_oscillation(total_steps, preset["num_cycles"], preset["pattern"])
    return [_interpolate_states(state_a, state_b, a) for a in alphas]


def _extract_visual_vocabulary_from_params(state: dict, strength: float = 1.0) -> dict:
    """
    Phase 2.7: Extract image-generation vocabulary from a 5D parameter state.
    Uses nearest-neighbour matching with Euclidean distance.
    strength ∈ [0,1] controls how many keywords are returned.
    """
    nn = _find_nearest_visual_type(state)
    # Scale keywords by strength: at strength=1 return all, at 0.3 return ~2
    n_kw = max(2, int(len(nn["keywords"]) * strength))
    return {
        "nearest_type": nn["nearest_type"],
        "distance": nn["distance"],
        "keywords": nn["keywords"][:n_kw],
        "strength": round(strength, 3),
    }


def _build_composite_prompt(state: dict) -> str:
    """
    Phase 2.7: Build a single composite image-generation prompt from a 5D state.
    """
    vocab = _extract_visual_vocabulary_from_params(state, strength=1.0)
    return ", ".join(vocab["keywords"])


def _build_split_view_prompt(multi_domain_state: dict) -> dict:
    """
    Phase 2.7: Build per-domain prompts for split-view composition.
    multi_domain_state maps domain_id -> {param: value} dicts.
    Only processes the 'illustrative' key.
    """
    if "illustrative" not in multi_domain_state:
        return {"error": "No 'illustrative' key in multi-domain state"}
    return {
        "domain": "illustrative",
        "prompt": _build_composite_prompt(multi_domain_state["illustrative"]),
        "vocabulary": _extract_visual_vocabulary_from_params(
            multi_domain_state["illustrative"]
        ),
    }


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


def get_style_parameters(style: str) -> dict:
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
        f"{', '.join(ILLUSTRATION_TAXONOMY.keys())}"
    )


def format_parameters_as_prompt_elements(params: dict) -> str:
    """Convert locked parameters to prompt-friendly text elements."""
    elements = []
    
    for category, items in params.items():
        if category == "style_name":
            continue
        if isinstance(items, list):
            elements.append(", ".join(items))
    
    return ". ".join(elements) + "."


# ============================================================================
# MCP SERVER INITIALIZATION
# ============================================================================

mcp = FastMCP("illustrative_vocabulary_mcp")


# ============================================================================
# LAYER 2: DETERMINISTIC TOOLS (Pure taxonomy operations)
# ============================================================================

@mcp.tool()
def get_style_taxonomy(illustration_style: str) -> str:
    """
    Retrieve locked visual parameters for a specific illustration style.
    
    This is LAYER 2 - pure deterministic taxonomy lookup with zero LLM cost.
    Returns all visual parameters that prevent style drift for the chosen style.
    
    Args:
        illustration_style: Target style (comic_book, children_book, technical, fashion, watercolor, concept_art)
    
    Returns:
        str: JSON with locked visual parameters for the illustration style
    """
    try:
        style_params = get_style_parameters(illustration_style)
        
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


@mcp.tool()
def list_available_styles() -> str:
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


@mcp.tool()
def compare_styles(style1: str, style2: str) -> str:
    """
    Compare visual parameters between two illustration styles.
    
    LAYER 2 - Pure deterministic comparison, no LLM cost.
    Useful for understanding differences and preventing unintended style drift.
    
    Args:
        style1: First style to compare
        style2: Second style to compare
    
    Returns:
        str: JSON with side-by-side parameter comparison
    """
    try:
        style1_params = get_style_parameters(style1)
        style2_params = get_style_parameters(style2)
        
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


@mcp.tool()
def override_parameters(illustration_style: str, override_color_strategy: list = None, 
                       override_lighting: list = None, override_edges: list = None) -> str:
    """
    Create a custom parameter set by overriding specific aspects of a base style.
    
    LAYER 2 - Deterministic composition of taxonomy elements.
    Allows users to mix-and-match locked parameters while maintaining consistency.
    
    Args:
        illustration_style: Base style to start from
        override_color_strategy: Optional list of color strategy descriptions to override
        override_lighting: Optional list of lighting descriptions to override
        override_edges: Optional list of edge descriptions to override
    
    Returns:
        str: JSON with modified parameter set
    """
    try:
        base_params = get_style_parameters(illustration_style)
        
        # Apply overrides
        result = base_params.copy()
        
        if override_color_strategy:
            result["color_strategy"] = override_color_strategy
        
        if override_lighting:
            result["lighting_model"] = override_lighting
        
        if override_edges:
            result["edge_treatment"] = override_edges
        
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

@mcp.tool()
def get_style_details(illustration_style: str) -> str:
    """
    Get comprehensive details about a specific illustration style.
    
    Includes all locked parameters, negative prompt elements, and usage guidance.
    
    Args:
        illustration_style: Illustration style to detail
    
    Returns:
        str: JSON with complete style specification
    """
    try:
        style_params = get_style_parameters(illustration_style)
        
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


@mcp.tool()
def export_prompt_elements(illustration_style: str) -> str:
    """
    Export locked parameters as prompt-friendly text elements.
    
    Returns a formatted string ready to embed in image generation prompts.
    These elements are locked to prevent the lighting/style drift Koray experienced.
    
    Args:
        illustration_style: Illustration style to export
    
    Returns:
        str: Formatted prompt elements and negative prompt
    """
    try:
        style_params = get_style_parameters(illustration_style)
        
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


# ============================================================================
# PHASE 2.6: RHYTHMIC COMPOSITION TOOLS (Layer 2 - zero LLM cost)
# ============================================================================

@mcp.tool()
def get_server_info() -> str:
    """
    Get server metadata, capabilities, and Phase 2.6/2.7 status.

    LAYER 2 - Pure deterministic lookup, zero LLM cost.

    Returns:
        str: JSON with server info including phase status and domain config.
    """
    return json.dumps({
        "server": "illustrative_vocabulary_mcp",
        "version": "2.7.0",
        "description": (
            "Illustrative Visual Vocabulary MCP with Phase 2.6 rhythmic "
            "presets and Phase 2.7 attractor visualization prompt generation. "
            "Maps illustration styles to a 5D normalised morphospace for "
            "cross-domain compositional emergence."
        ),
        "architecture": {
            "layer_1": "Pure taxonomy/enumeration lookup",
            "layer_2": "Deterministic computation (zero LLM cost) - Phase 2.6/2.7 tools",
            "layer_3": "Claude synthesis/creative operations (token cost)",
        },
        "phase_2_6_enhancements": {
            "rhythmic_presets": True,
            "preset_count": len(ILLUSTRATIVE_RHYTHMIC_PRESETS),
            "periods": sorted(set(
                p["steps_per_cycle"]
                for p in ILLUSTRATIVE_RHYTHMIC_PRESETS.values()
            )),
            "patterns": ["sinusoidal", "triangular", "square"],
        },
        "phase_2_7_enhancements": {
            "attractor_visualization": True,
            "visual_type_count": len(ILLUSTRATIVE_VISUAL_TYPES),
            "prompt_modes": ["composite", "split_view", "sequence"],
        },
        "morphospace": {
            "dimensions": 5,
            "parameter_names": ILLUSTRATIVE_PARAMETER_NAMES,
            "canonical_states": list(ILLUSTRATIVE_COORDS.keys()),
        },
    }, indent=2)


@mcp.tool()
def get_illustrative_coordinates(state_name: str) -> str:
    """
    Extract normalised 5D parameter coordinates for a canonical illustration
    style or return coordinates for all states.

    LAYER 2 - Pure deterministic lookup, zero LLM cost.

    Args:
        state_name: Canonical style name (comic_book, children_book, technical,
                    fashion, watercolor, concept_art) or 'all' for every state.

    Returns:
        str: JSON with normalised 5D coordinates.
    """
    if state_name == "all":
        return json.dumps({
            "parameter_names": ILLUSTRATIVE_PARAMETER_NAMES,
            "states": ILLUSTRATIVE_COORDS,
        }, indent=2)

    if state_name not in ILLUSTRATIVE_COORDS:
        return json.dumps({
            "error": f"Unknown state '{state_name}'",
            "available": list(ILLUSTRATIVE_COORDS.keys()),
        }, indent=2)

    return json.dumps({
        "state": state_name,
        "parameter_names": ILLUSTRATIVE_PARAMETER_NAMES,
        "coordinates": ILLUSTRATIVE_COORDS[state_name],
    }, indent=2)


@mcp.tool()
def get_illustrative_visual_types() -> str:
    """
    List all visual types with their 5D coordinates and image-generation keywords.

    LAYER 2 - Pure deterministic lookup, zero LLM cost.

    Returns:
        str: JSON with visual type catalogue including coordinates and keywords.
    """
    types_out = {}
    for vtype, vdata in ILLUSTRATIVE_VISUAL_TYPES.items():
        types_out[vtype] = {
            "coordinates": vdata["coords"],
            "keywords": vdata["keywords"],
        }
    return json.dumps({
        "visual_types": types_out,
        "parameter_names": ILLUSTRATIVE_PARAMETER_NAMES,
        "total": len(types_out),
    }, indent=2)


@mcp.tool()
def compute_illustrative_trajectory(
    state_a_name: str,
    state_b_name: str,
    num_steps: int = 48,
    pattern: str = "sinusoidal",
) -> str:
    """
    Compute smooth interpolation trajectory between two canonical illustration
    states in normalised 5D parameter space.

    LAYER 2 - Deterministic computation, zero LLM cost.
    Uses forced orbit integration (phase arithmetic + interpolation).

    Args:
        state_a_name: Start state (e.g. 'comic_book').
        state_b_name: End state (e.g. 'watercolor').
        num_steps: Total trajectory length.
        pattern: Oscillation pattern ('sinusoidal', 'triangular', 'square').

    Returns:
        str: JSON with trajectory points and per-step vocabulary.
    """
    if state_a_name not in ILLUSTRATIVE_COORDS:
        return json.dumps({"error": f"Unknown state '{state_a_name}'",
                           "available": list(ILLUSTRATIVE_COORDS.keys())}, indent=2)
    if state_b_name not in ILLUSTRATIVE_COORDS:
        return json.dumps({"error": f"Unknown state '{state_b_name}'",
                           "available": list(ILLUSTRATIVE_COORDS.keys())}, indent=2)

    state_a = ILLUSTRATIVE_COORDS[state_a_name]
    state_b = ILLUSTRATIVE_COORDS[state_b_name]
    alphas = _generate_oscillation(num_steps, 1.0, pattern)

    trajectory = []
    for i, a in enumerate(alphas):
        pt = _interpolate_states(state_a, state_b, a)
        nn = _find_nearest_visual_type(pt)
        trajectory.append({
            "step": i,
            "alpha": round(a, 4),
            "coordinates": {p: round(pt[p], 4) for p in ILLUSTRATIVE_PARAMETER_NAMES},
            "nearest_visual_type": nn["nearest_type"],
            "distance_to_type": nn["distance"],
        })

    return json.dumps({
        "state_a": state_a_name,
        "state_b": state_b_name,
        "pattern": pattern,
        "num_steps": num_steps,
        "trajectory": trajectory,
    }, indent=2)


@mcp.tool()
def apply_illustrative_rhythmic_preset(preset_name: str) -> str:
    """
    Apply a Phase 2.6 rhythmic preset, generating a complete oscillation
    trajectory with per-step visual vocabulary.

    LAYER 2 - Deterministic forced orbit integration, zero LLM cost.
    Guaranteed periodic closure (zero drift).

    Args:
        preset_name: Preset identifier (edge_contrast_sweep, warmth_cycle,
                     painterly_pulse, atmosphere_drift, medium_transition,
                     editorial_shift, texture_oscillation).

    Returns:
        str: JSON with full trajectory, period, vocabulary per step.
    """
    if preset_name not in ILLUSTRATIVE_RHYTHMIC_PRESETS:
        return json.dumps({
            "error": f"Unknown preset '{preset_name}'",
            "available": list(ILLUSTRATIVE_RHYTHMIC_PRESETS.keys()),
        }, indent=2)

    preset = ILLUSTRATIVE_RHYTHMIC_PRESETS[preset_name]
    traj = _generate_preset_trajectory(preset_name)
    total_steps = len(traj)

    steps_out = []
    for i, pt in enumerate(traj):
        nn = _find_nearest_visual_type(pt)
        steps_out.append({
            "step": i,
            "cycle": i // preset["steps_per_cycle"],
            "phase_in_cycle": i % preset["steps_per_cycle"],
            "coordinates": {p: round(pt[p], 4) for p in ILLUSTRATIVE_PARAMETER_NAMES},
            "nearest_visual_type": nn["nearest_type"],
            "distance_to_type": nn["distance"],
            "keywords": nn["keywords"][:4],
        })

    return json.dumps({
        "preset": preset_name,
        "description": preset["description"],
        "state_a": preset["state_a"],
        "state_b": preset["state_b"],
        "pattern": preset["pattern"],
        "period": preset["steps_per_cycle"],
        "num_cycles": preset["num_cycles"],
        "total_steps": total_steps,
        "trajectory": steps_out,
    }, indent=2)


@mcp.tool()
def list_illustrative_rhythmic_presets() -> str:
    """
    List all available Phase 2.6 rhythmic presets with period, pattern,
    state endpoints, and cross-domain synchronisation notes.

    LAYER 2 - Pure enumeration, zero LLM cost.

    Returns:
        str: JSON catalogue of all rhythmic presets.
    """
    presets_out = []
    for name, cfg in ILLUSTRATIVE_RHYTHMIC_PRESETS.items():
        presets_out.append({
            "name": name,
            "period": cfg["steps_per_cycle"],
            "pattern": cfg["pattern"],
            "state_a": cfg["state_a"],
            "state_b": cfg["state_b"],
            "num_cycles": cfg["num_cycles"],
            "total_steps": cfg["num_cycles"] * cfg["steps_per_cycle"],
            "description": cfg["description"],
        })

    periods = sorted(set(p["period"] for p in presets_out))
    return json.dumps({
        "presets": presets_out,
        "total": len(presets_out),
        "periods": periods,
        "period_strategy": {
            "overlaps": {
                15: "nuclear, catastrophe, diatom",
                18: "nuclear, catastrophe, diatom",
                20: "microscopy, catastrophe, diatom",
                22: "catastrophe, heraldic",
            },
            "gap_fillers": {
                11: "fills gap 10-12",
                14: "fills gap 12-15",
                26: "fills gap 25-30",
            },
        },
    }, indent=2)


# ============================================================================
# PHASE 2.7: ATTRACTOR VISUALIZATION PROMPT GENERATION (Layer 2)
# ============================================================================

@mcp.tool()
def generate_illustrative_attractor_prompt(
    edge_definition: float,
    color_richness: float,
    texture_organicity: float,
    lighting_drama: float,
    depth_atmosphere: float,
    mode: str = "composite",
    strength: float = 1.0,
) -> str:
    """
    Generate image-generation-ready prompts from 5D illustrative coordinates.

    LAYER 2 - Deterministic nearest-neighbour vocabulary extraction, zero LLM
    cost.  Suitable for ComfyUI, Stable Diffusion, DALL-E prompt fields.

    Three modes:
      composite  – single blended prompt string
      split_view – per-domain prompt (for multi-domain compositions)
      sequence   – keyframe prompts at 25%, 50%, 75% interpolation toward
                   the nearest canonical state

    Args:
        edge_definition:    0.0 (soft/diffuse)   → 1.0 (hard/precise)
        color_richness:     0.0 (monochrome)      → 1.0 (rich/saturated)
        texture_organicity: 0.0 (smooth/digital)  → 1.0 (organic/painterly)
        lighting_drama:     0.0 (even/functional)  → 1.0 (dramatic/cinematic)
        depth_atmosphere:   0.0 (flat/isometric)   → 1.0 (atmospheric/volumetric)
        mode: 'composite', 'split_view', or 'sequence'.
        strength: 0.0-1.0 controls keyword density (1.0 = full vocabulary).

    Returns:
        str: JSON with image-generation prompt(s) and vocabulary metadata.
    """
    state = {
        "edge_definition": max(0.0, min(1.0, edge_definition)),
        "color_richness": max(0.0, min(1.0, color_richness)),
        "texture_organicity": max(0.0, min(1.0, texture_organicity)),
        "lighting_drama": max(0.0, min(1.0, lighting_drama)),
        "depth_atmosphere": max(0.0, min(1.0, depth_atmosphere)),
    }

    vocab = _extract_visual_vocabulary_from_params(state, strength=strength)

    if mode == "composite":
        prompt = ", ".join(vocab["keywords"])
        return json.dumps({
            "mode": "composite",
            "prompt": prompt,
            "vocabulary": vocab,
            "coordinates": state,
        }, indent=2)

    elif mode == "split_view":
        prompt = ", ".join(vocab["keywords"])
        return json.dumps({
            "mode": "split_view",
            "domain": "illustrative",
            "prompt": prompt,
            "vocabulary": vocab,
            "coordinates": state,
            "usage": (
                "Combine with prompts from other aesthetic domains "
                "(microscopy, nuclear, heraldic, etc.) for multi-domain "
                "split-view composition."
            ),
        }, indent=2)

    elif mode == "sequence":
        # Keyframes at 25%, 50%, 75% interpolation toward nearest type
        target_coords = ILLUSTRATIVE_VISUAL_TYPES[vocab["nearest_type"]]["coords"]
        keyframes = []
        for pct in [0.25, 0.50, 0.75, 1.00]:
            interp = _interpolate_states(state, target_coords, pct)
            kf_vocab = _extract_visual_vocabulary_from_params(interp, strength=strength)
            keyframes.append({
                "interpolation_pct": pct,
                "coordinates": {p: round(interp[p], 4) for p in ILLUSTRATIVE_PARAMETER_NAMES},
                "prompt": ", ".join(kf_vocab["keywords"]),
                "nearest_type": kf_vocab["nearest_type"],
            })
        return json.dumps({
            "mode": "sequence",
            "origin": state,
            "target_type": vocab["nearest_type"],
            "keyframes": keyframes,
        }, indent=2)

    else:
        return json.dumps({
            "error": f"Unknown mode '{mode}'",
            "available_modes": ["composite", "split_view", "sequence"],
        }, indent=2)


@mcp.tool()
def get_illustrative_domain_registry_config() -> str:
    """
    Return Tier 4D integration configuration for compositional limit cycle
    discovery.  Exports the domain's periods, parameter names, canonical
    state coordinates, and predicted emergent attractor contributions so
    that aesthetic-dynamics-core can include this domain in multi-domain
    composition experiments.

    LAYER 2 - Pure deterministic export, zero LLM cost.

    Returns:
        str: JSON with complete domain registry configuration.
    """
    periods = sorted(set(
        p["steps_per_cycle"] for p in ILLUSTRATIVE_RHYTHMIC_PRESETS.values()
    ))

    # Predict emergent attractor contributions based on period interactions
    # with known cross-domain periods
    cross_domain_periods = {
        "microscopy": [10, 16, 20, 24, 30],
        "nuclear": [15, 18],
        "catastrophe": [15, 18, 20, 22, 25],
        "diatom": [12, 15, 18, 20, 30],
        "heraldic": [12, 16, 22, 25, 30],
    }

    predicted_emergent = []

    # LCM synchronisations with other domains
    for other_domain, other_periods in cross_domain_periods.items():
        for op in other_periods:
            for mp in periods:
                lcm_val = _lcm(op, mp)
                if lcm_val <= 80:
                    predicted_emergent.append({
                        "type": "lcm_sync",
                        "period": lcm_val,
                        "domains": ["illustrative", other_domain],
                        "source_periods": [mp, op],
                        "basin_size_estimate": round(
                            0.02 + 0.06 * (1.0 / (lcm_val / 30.0)), 3
                        ),
                    })

    # Gap-fillers this domain enables
    all_periods = sorted(set(periods))
    for i in range(len(all_periods) - 1):
        gap = all_periods[i + 1] - all_periods[i]
        if gap >= 2:
            mid = (all_periods[i] + all_periods[i + 1]) // 2
            predicted_emergent.append({
                "type": "gap_filler",
                "period": mid,
                "gap": f"{all_periods[i]}-{all_periods[i+1]}",
                "basin_size_estimate": round(0.01 + 0.03 * gap, 3),
            })

    # De-duplicate by period
    seen_periods = set()
    unique_emergent = []
    for pe in sorted(predicted_emergent, key=lambda x: -x["basin_size_estimate"]):
        if pe["period"] not in seen_periods:
            seen_periods.add(pe["period"])
            unique_emergent.append(pe)

    return json.dumps({
        "domain_id": "illustrative",
        "display_name": "Illustrative Visual Vocabulary",
        "mcp_server": "illustrative_vocabulary_mcp",
        "parameter_names": ILLUSTRATIVE_PARAMETER_NAMES,
        "canonical_states": list(ILLUSTRATIVE_COORDS.keys()),
        "periods": periods,
        "preset_count": len(ILLUSTRATIVE_RHYTHMIC_PRESETS),
        "visual_type_count": len(ILLUSTRATIVE_VISUAL_TYPES),
        "tier_4d_integration": {
            "state_coordinates": ILLUSTRATIVE_COORDS,
            "presets": {
                name: {
                    "period": cfg["steps_per_cycle"],
                    "state_a": cfg["state_a"],
                    "state_b": cfg["state_b"],
                    "pattern": cfg["pattern"],
                }
                for name, cfg in ILLUSTRATIVE_RHYTHMIC_PRESETS.items()
            },
        },
        "predicted_emergent_attractors": unique_emergent[:12],
        "cross_domain_sync_periods": {
            15: ["nuclear", "catastrophe", "diatom"],
            18: ["nuclear", "catastrophe", "diatom"],
            20: ["microscopy", "catastrophe", "diatom"],
            22: ["catastrophe", "heraldic"],
        },
    }, indent=2)


def _lcm(a: int, b: int) -> int:
    """Least common multiple of two positive integers."""
    return abs(a * b) // math.gcd(a, b)


if __name__ == "__main__":
    mcp.run()
