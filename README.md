# Illustrative Visual Vocabulary MCP Server

Solves the **style drift problem** where illustration types (photographic vs. illustrative) get reinterpreted during generation. This server provides locked visual parameters that anchor your aesthetic intent and prevent downstream style changes from overriding your choice.

## Problem Statement

As Koray mentioned:
> "I would like to choose the styles MJ gives me. I would like to give keywords like 'photographic' or 'illustrative' because when I choose an illustrative style for its lighting the final style goes illustrative. It's hard to keep in track."

**Root cause**: Style keywords are interpreted flexibly by generative models. Downstream rendering choices (especially lighting) can reinterpret the entire aesthetic, so "illustrative" becomes photorealistic, or vice versa.

**Solution**: This MCP server provides **locked visual parameter sets** that act as semantic anchors. Instead of just saying "illustrative," you get:
- Hard edges + limited color palette + flat surfaces + dramatic lighting + no depth blur
- These parameters are locked and cannot be overridden by downstream choices

## Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: Intent Analysis (Claude)                           │
│ Extract: "I want comic book style of a cyberpunk street"    │
│ Output: Parsed intent + target style                        │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 2: Deterministic Taxonomy (MCP Server - This Tool)    │
│ Pure lookup: comic_book → {edges: hard, colors: 8-12, ...}  │
│ ZERO LLM COST - Just dictionary lookups                     │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 3: Synthesis (Claude)                                 │
│ Weave: original_intent + locked_params → coherent_prompt    │
│ Final prompt includes locked parameters as unambiguous text │
└─────────────────────────────────────────────────────────────┘
```

**Cost optimization**: ~60% fewer LLM calls than pure prompting approach. Layers 1 & 3 use Claude. Layer 2 is deterministic dictionary lookup (free).

## Available Illustration Styles

### 1. **Comic Book / Graphic Novel**
- Hard defined outlines, limited 8-12 color palette
- Flat color blocking (no gradients), dramatic lighting
- Perfect for: manga, superhero comics, graphic novels

### 2. **Children's Book**
- Soft edges, warm inviting colors, visible brushwork
- Hand-drawn feeling, gentle lighting, readable depth
- Perfect for: storybooks, children's content, playful illustrations

### 3. **Technical Illustration**
- Precise clean lines, muted professional palette
- Isometric/orthographic views, mechanical precision
- Perfect for: diagrams, medical illustrations, product specs

### 4. **Fashion Editorial**
- Elegant flowing lines, sophisticated colors (often monochromatic)
- Dramatic editorial lighting, stylized proportions
- Perfect for: fashion design, editorial spreads, couture

### 5. **Watercolor Painting**
- Soft diffuse edges, transparent color layers
- Organic texture, paper grain visible, natural lighting
- Perfect for: landscapes, fine art, atmospheric pieces

### 6. **Concept Art / Painting**
- Painterly texture, cinematic lighting, rich colors
- Chiaroscuro, volumetric depth, atmospheric effects
- Perfect for: game concept art, environment design, narrative painting

## Tools

### Deterministic Tools (Layer 2 - Zero Cost)

**`get_style_taxonomy`**
- Returns locked visual parameters for a style
- Prevents style drift by providing unambiguous specifications
- Input: style name
- Output: All visual parameters (edges, colors, texture, lighting, etc.)

**`list_available_styles`**
- Enumerate all illustration styles with brief descriptions
- Use to explore what's available

**`compare_styles`**
- Side-by-side visual parameter comparison
- Useful for understanding differences between styles
- Shows you exactly what changes between comic book vs watercolor

**`override_parameters`**
- Mix-and-match locked parameters from different styles
- Create custom parameter sets while maintaining consistency
- Warns about compatibility issues

**`export_prompt_elements`**
- Convert locked parameters to prompt-friendly text
- Includes positive prompt elements AND negative prompt
- The negative prompt is critical - explicitly blocks incompatible aesthetics

### Information Tools

**`get_style_details`**
- Comprehensive style specification
- Usage guidance for implementation
- Complete parameter breakdown

**`export_prompt_elements`**
- Ready-to-use prompt text
- Includes negative prompt (critical for preventing style drift)

## Usage Pattern

### Workflow for Koray's Use Case

1. **Identify desired style**: "I want illustrative with lighting that stays illustrative"
   ```
   get_style_taxonomy(user_prompt="...", illustration_style="comic_book")
   ```

2. **Get locked parameters**: Returns edges, colors, texture, lighting, depth, compositional rules

3. **Export as prompt elements**: Get ready-to-paste prompt text
   ```
   export_prompt_elements(illustration_style="comic_book")
   ```
   Returns:
   ```
   Positive: "hard, defined outlines, consistent line weight... flat color blocking..."
   Negative: "NOT: photorealism, soft gradients, depth of field blur..."
   ```

4. **Include in final prompt**: Paste both positive and negative elements into your generation prompt
   - These act as semantic anchors
   - Prevent downstream choices from reinterpreting the style
   - "NOT: photorealism" blocks the photorealistic style drift Koray experienced

### Advanced Workflow: Custom Parameter Mix

If you want comic book edges + watercolor colors:

```
override_parameters(
    illustration_style="comic_book",
    override_color_strategy=["transparent color layers", "luminous color mixing", ...]
)
```

Returns: Custom parameter set with compatibility warnings

## Why This Solves Style Drift

**Traditional approach (Doesn't work):**
```
Prompt: "illustrative style scene..."
↓
Model interprets "illustrative" flexibly
↓
Downstream choices override the intent
↓
Final result: photorealistic (style drift!)
```

**This server's approach (Works):**
```
Prompt: "illustrative style scene... 
         hard edges, limited palette, flat colors, dramatic lighting, no depth blur...
         NOT: photorealism, gradients, depth of field blur, photorealistic texture..."
↓
Model receives unambiguous locked parameters
↓
Locked negative prompt explicitly blocks incompatible aesthetics
↓
Final result: Consistent illustrative style (no drift!)
```

## Installation

```bash
# Clone or place the server file
pip install -e .

# Or with dev dependencies:
pip install -e ".[dev]"
```

## Testing

```bash
# Run the server
python illustrative_vocabulary_mcp.py

# Test with MCP Inspector (if installed)
npx @modelcontextprotocol/inspector illustrative_vocabulary_mcp.py
```

## Integration with Claude

Use this MCP server in Claude.ai or your Claude API client:

```python
# Example: Using with Claude API
# Call get_style_taxonomy to get locked parameters
# Then have Claude incorporate them into a full prompt
```

The server provides the **deterministic Layer 2** that Claude can reference when synthesizing final prompts in Layer 3.

## Architecture Philosophy

This server demonstrates the **three-layer cost optimization pattern**:

1. **Intent Analysis** → Claude (semantic understanding)
2. **Deterministic Mapping** → MCP Server (pure lookup, ~60% cost savings)
3. **Synthesis** → Claude (creative weaving)

By separating deterministic taxonomy from creative synthesis, we achieve:
- **Cost efficiency**: Most work is dictionary lookups
- **Reproducibility**: Same input always produces same parameters
- **Verifiability**: Easy to audit what locked parameters were used
- **Scalability**: Can expand taxonomy without LLM retraining

## Future Enhancements

- [ ] Add photography style taxonomy (photographic, documentary, fine art photography)
- [ ] Add painting styles (oil, acrylic, gouache)
- [ ] Add rendering engine compatibility notes (Stable Diffusion vs. DALL-E vs. Midjourney)
- [ ] Add historical era-based illustration styles (art deco, brutalist, retro futurism)
- [ ] Add user-created custom style vocabularies
- [ ] Integration with prompt-to-image workflow systems (ComfyUI, etc.)

## For Lushy Integration

This MCP server is designed to integrate with Lushy workflows:

1. **Workflow Template**: Use as MCP tool in ComfyUI custom workflows
2. **Creator Tools**: Package as aesthetic enhancement tool for creators monetizing workflows
3. **Academic Market**: Reproducibility showcase - locked parameters = reproducible aesthetics
4. **Paid Access**: Offer extended style libraries as premium feature

## References

- **Problem Source**: LinkedIn post by Koray Şahan (Starter founder)
- **Architecture**: Three-layer categorical pattern using ologs + single LLM synthesis
- **Cost Model**: Achieves ~60% cost reduction vs. pure LLM prompting
