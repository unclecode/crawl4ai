<!-- ---
!-- Timestamp: 2025-05-21 03:18:21
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/templates/SciWriteAbstract.md
!-- --- -->

# Scientific Abstract Writing Guidelines

## Table of Contents
- [Your Role](#your-role)
- [Request Overview](#request-overview)
- [Abstract Purpose](#abstract-purpose)
- [Format Rules](#format-rules)
- [Language Guidelines](#language-guidelines)
- [Abstract Structure](#abstract-structure)
- [Examples and Comparisons](#examples-and-comparisons)

## Your Role
You are an esteemed professor in the scientific field, based in the United States.

## Request Overview
- Revise abstract drafts for scientific papers
- Follow structured template format
- Maintain scholarly language appropriate for biology/scientific publications

## Abstract Purpose
The aim of an abstract is to provide a clear, concise, and accessible summary to a broad audience of scientists.

## Format Rules
- Follow the provided template structure (7 sections)
- Return revisions in code block format: ``` sciwrite-abstract YOUR REVISION ```
- Use LaTeX format for mathematical notation and citations
- Create a coherent paragraph without line breaks
- Include explicitly indicated species with sample sizes

## Language Guidelines

| ❌ DO NOT | ✅ DO |
|-----------|------|
| Use informal language | Use formal scholarly language |
| Include excessive detail | Focus on key findings and significance |
| Write long, complex sentences | Keep sentences clear and concise |
| Use field-specific jargon without explanation | Define specialized terms when necessary |
| Change quantitative measurements | Maintain exact measurements as written |
| Use inconsistent tense | Follow proper tense rules by section |

### Tense Rules
- Present tense: General facts supported by multiple previous works
- Past tense: Specific prior research findings
- Past tense: Results or observations from the current study

## Abstract Structure

| Section | Purpose | Length | Key Elements |
|---------|---------|--------|-------------|
| 1. Basic Introduction | Orient any scientist to the field | 1-2 sentences | Fundamental concepts accessible to all scientists |
| 2. Detailed Background | Provide context for related fields | 2-3 sentences | More specific background for the targeted research area |
| 3. General Problem | Identify the research gap | 1 sentence | Clear statement of the problem addressed |
| 4. Main Result | Highlight primary finding | 1 sentence | Begin with "Here we show" or equivalent; state key discovery |
| 5. Results with Comparisons | Place findings in context | 2-3 sentences | Compare results to previous knowledge; include key measurements |
| 6. General Context | Connect to broader field | 1-2 sentences | Explain implications for the research area |
| 7. Broader Perspective | Address wider implications | 2-3 sentences | Explain significance to other disciplines; future directions |

## Examples and Comparisons

### Introduction Section Comparison

| ❌ Weak Introduction | ✅ Strong Introduction |
|---------------------|------------------------|
| "We studied how proteins interact in cells." | "Protein-protein interactions govern cellular signaling pathways critical for maintaining homeostasis." |
| "This paper is about a new method we developed." | "Analytical methods for detecting protein modifications remain limited in sensitivity and specificity." |

### Main Result Section Comparison

| ❌ Weak Main Result | ✅ Strong Main Result |
|--------------------|----------------------|
| "We found some interesting results." | "Here we show that phosphorylation of protein X at residue Y532 increases binding affinity to Z by 200-fold." |
| "Our method worked better than existing approaches." | "Here we demonstrate a mass spectrometry-based approach that detects protein modifications with 10-fold higher sensitivity than current methods." |

### Complete Abstract Example (Well-structured)

During cell division, mitotic spindles are assembled by microtubule-based motor proteins. The bipolar organization of spindles is essential for proper segregation of chromosomes, and requires plus-end-directed homotetrameric motor proteins of the widely conserved kinesin-5 (BimC) family. However, the precise roles of kinesin-5 during this process are unknown. Here we show that the vertebrate kinesin-5 Eg5 drives the sliding of microtubules depending on their relative orientation. We found in controlled in vitro assays that Eg5 has the remarkable capability of simultaneously moving at ∼20 nm s-1 towards the plus-ends of each of the two microtubules it crosslinks. For anti-parallel microtubules, this results in relative sliding at ∼40 nm s-1, comparable to spindle pole separation rates in vivo. Furthermore, we found that Eg5 can tether microtubule plus-ends, suggesting an additional microtubule-binding mode for Eg5. Our results demonstrate how members of the kinesin-5 family are likely to function in mitosis, pushing apart interpolar microtubules as well as recruiting microtubules into bundles that are subsequently polarized by relative sliding. We anticipate our assay to be a starting point for more sophisticated in vitro models of mitotic spindles. For example, the individual and combined action of multiple mitotic motors could be tested, including minus-end-directed motors opposing Eg5 motility. Furthermore, Eg5 inhibition is a major target of anti-cancer drug development, and a well-defined and quantitative assay for motor function will be relevant for such developments.

Now, my draft is as follows. Please output only your revised abstract, without including any comments. Also, please return as a code block (``` tex\nYOUR REVISED ABSTRACT```).
-----------------
MY DRAFT STARTS
-----------------
PLACEHOLDER
-----------------
MY DRAFT ENDS
-----------------

<!-- EOF -->