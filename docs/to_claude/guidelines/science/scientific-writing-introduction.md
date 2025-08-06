<!-- ---
!-- title: ./genai/templates/SciWriteIntroduction.md
!-- author: ywatanabe
!-- date: 2024-11-19 22:21:24
!-- --- -->


----------
Background
----------
# Your Role
You are an esteemed professor in the scientific field, based in the United States.

# My Request
- Please revise my introduction draft.

# Aim of Introduction
The aim of introduction is to offer readers with the background necessary to understand your paper: the status of knowledge in your field, the question motivating your work and its significance, how you sought to answer that question (methods), and your main findings. A well-written introduction will broaden your readership by making your findings accessible to a larger audience.

# Rules
- Style
  - Please follow the format of the template I will provide below in this message.
  - Your revision should conform to the language style typical of a scholarly article in biology.
  - Use technical language suitable for neuroscience journals 
  - Spell out abbreviations and acronyms in their first appearance
  - Include a clear, concise topic sentence in each paragraph.
  - Use transition phrases between paragraphs to make introduction coherent and cohesive
  - Insert a newline with the tab identation between pargraphs, except for between the first and second paragraphs;both [1. Opening Statement] and [2. Importance of the Field] sections should be in the first paragraph.

- Volume
  - Ensure to write at least 1000 words

- Misc.
  - Explicitly indicate species with sample sizes
  - Add relevant references when applicable
  - Keep existing references as they are
  - Maintain quantitative measurements as they are written.
  - Target audience is neuroscience/psychology specialists
  - Pay careful attention to the use of hyphens, en dashes, em dashes, and minus signs.
  - Avoid unnercessary adjectives for emphasizing like "significantly", "well", 
  - If tex tags are inserted, please conform to the latex style.

- Return as code block (for just convenience for selection) like this:
  ``` sciwrite-introduction
  YOUR REVISION
  ```
- Use LaTeX format

- When adding references (to literature, tables, or figures) will enhance the quality of the paper, please insert a placeholder using this LaTeX command `\hlref{XXX}`. This command will highlight any unlinked content so that it will work well as a placeholder.

Now, the template is as follows:
------------------
TEMPLATE STARTS
------------------
[1. Opening Statement]
The introduction should commence with a broad yet detailed statement about the field of study. It's essential to set the stage for the research, making it engaging and accessible for a general scientific audience while retaining technical accuracy. This part is the first half of the opening paragraph.

[2. Importance of the Field]
The second half of the opening paragraph should emphasize the importance and relevance of the field. It's crucial to highlight the potential impact of the research area, its significance in advancing scientific knowledge, and its applications in real-world scenarios.

[3. Existing Knowledge and Gaps]
In the next 1-2 paragraphs, provide a comprehensive summary of the current state of knowledge in the field. This section should identify key gaps or unanswered questions in the existing research, using precise data and measurements where relevant. It sets up the context and necessity for your research, outlining why your study is both timely and important.

[4. Limitations in Previous Works]
In the next 1-2 paragraphs, this section should critically examine the limitations inherent in previous research within the field. Discuss methodological constraints, such as the use of specific models (e.g., animal models in neuroscience) or tools (like imaging techniques), which may have restricted the scope or applicability of the findings. Additionally, address any logical shortcomings or gaps in previous studies, such as unexplored variables, overlooked correlations, or assumptions that may have influenced the outcomes. Highlighting these limitations not only sets the stage for your research contribution but also contextualizes your work within the broader field, establishing the necessity for your approach and methodology.

[5. Research Question or Hypothesis]
Dedicate one paragraph to clearly stating the research question or hypothesis of your study. This should be specific, directly related to the gaps identified, and framed in a way that highlights its significance in the broader context of the field.

[6. Approach and Methods]
Describe the approach and methods used in your research, in one paragraph. This section should give an overview of the methods without delving into excessive detail, but maintain enough technicality to be clear and credible to a scientifically literate audience. Also, highlight the speriority of current study over existing works mensioned in the [3. Limitations in Previous Work].

[7. Overview of Results]
Optionally, include a paragraph providing a high-level summary of the main findings of your research. This should avoid detailed data but effectively convey the overall outcomes and achievements of the study.

[8. Significance and Implications]
Conclude with a separate, final paragraph of 1-3 sentences discussing the significance of your findings and their implications for the field. It should articulate how your research contributes to advancing knowledge and what it potentially means for future studies in the field.
----------------
TEMPLATE ENDS
----------------

For example, the introduction below is well-written, following the provided template.

----------------
EXAMPLE STARTS
----------------
[START of 1. Opening Statement] Dementia, which affects an estimated 50 million people worldwide, is a significant health challenge characterized by the progressive decline of memory, attention, and executive functions, which are pivotal for maintaining daily independence (Prince et al., 2015). [END of 1. Opening Statement] [START of 2. Importance of the Field] Accurate identification of its various subtypes, such as Alzheimer's disease (AD), dementia with Lewy bodies (DLB), and idiopathic normal-pressure hydrocephalus (iNPH), is crucial for appropriate clinical management (Barker et al., 2002; Williams and Malm, 2016; McKeith et al., 2017; Arvanitakis et al., 2019; Leuzy et al., 2022). [END of 2. Importance of the Field]

[START of 4. Limitations in Previous Works] The pursuit of early and precise differentiation of dementia subtypes is hindered by several factors. Traditional diagnostic techniques, such as magnetic resonance imaging (MRI), positron emission tomography (PET), and cerebrospinal fluid (CSF) tests, while effective, are costly, invasive, and not universally accessible, limiting their utility in certain regions (Garn et al., 2017; Hata et al., 2023). Moreover, the mild cognitive impairment (MCI) stage, often a precursor to dementia, presents a diagnostic challenge due to its subtle symptom presentation, complicating its diagnosis in clinical practice (Ieracitano et al., 2020). [END of 4. Limitations in Previous Works]

[START of 5. Research Question or Hypothesis] These issues underscore the necessity for a more accessible, noninvasive, and standardized screening tool capable of discerning the nuanced differences between dementia subtypes. [END of 5. Research Question or Hypothesis]

[START of 3. Existing Knowledge and Gaps] Further highlighting the urgency for early and accurate diagnosis, the recent identification of an antibody targeting amyloid beta protofibrils opens a promising avenue for decelerating the progression of AD in its nascent stages (Swanson et al., 2021). Furthermore, iNPH presents a unique case wherein early detection could lead to significant symptom relief through interventions such as CSF shunting, emphasizing the importance of precise early diagnostic techniques (Williams & Malm, 2016). [END of 3. Existing Knowledge and Gaps]

[Start of 6. Approach and Methods] Responding to the need for noninvasive, cost-effective, and widely available diagnostic methods, our research has pivoted toward the utilization of electroencephalography (EEG). This neurophysiological recording technique, renowned for its noninvasiveness and cost-effectiveness, holds untapped potential for enhancing the early detection and differentiation of dementia. [END of 6. Approach and Methods]

[START of 3. Existing Knowledge and Gaps] The EEG methods proposed by existing studies, however, have often been less successful in practical application due to limited comparative analyses being available in the literature, misapplication of machine learning techniques, e.g., the failure to appropriately segregate datasets from external institutions for independent testing compromises the assessment of a model's true classification accuracy across various clinical settings, and a dearth of generalizable findings (Rossini et al., 2008; Aoki et al., 2015; Bonanni et al., 2016; Ieracitano et al., 2020; Chatzikonstantinou et al., 2021; Sánchez-Reyes et al., 2021; Micchia et al., 2022). [END of 3. Existing Knowledge and Gaps]

[START of 6. Approach and Methods] A particularly promising yet underexplored domain is the use of deep convolutional neural networks (DCNNs) with EEG data for dementia classification; notably, this technique may bypass the intricacies of feature engineering and reveal the nuanced patterns indicative of various dementia subtypes. [END of 6. Approach and Methods]

In this study, we are committed to testing three pivotal hypotheses, each aimed at overcoming the challenges of early diagnosis of dementia and its diverse subtypes. Our first hypothesis contends that the proposed DCNN using EEG data can accurately distinguish between healthy volunteers (HVs) and patients with dementia across multiple institutions; verifying this hypothesis would indicate the robustness and wide applicability of our model. Our second hypothesis posits that this EEG-driven DCNN will be able to adeptly classify dementia subtypes (AD, DLB, or iNPH); evidence in support of this hypothesis would showcase the model's diagnostic precision. Last, our third hypothesis is that identifiable EEG patterns associated with dementia subtypes are anticipated to be present in the preceding MCI stages; if this is the case, it would suggest the existence of potential indicators that may provide insights into the progression from MCI to overt dementia. Our findings could mark a significant advancement in predictive diagnostics and tailor-made therapeutic interventions in the realm of neurodegenerative diseases.
----------------
EXAMPLE ENDS
----------------

Remember to insert the following section tags (START and END ) in the same manner as the above example:
([START of 1. Opening Statement], [END of 1. Opening Statement], [START of 2. Importance of the Field], [END of 2. Importance of the Field], [START of 3. Existing Knowledge and Gaps], [END of 3. Existing Knowledge and Gaps], [START of 4. Limitations in Previous Works], [END of 4. Limitations in Previous Works], [START of 5. Research Question or Hypothesis], [END of 5. Research Question or Hypothesis], [START of 6. Approach and Methods], [END of 6. Approach and Methods], [START of 7. Overview of Results], [END of 7. Overview of Results], [START of 8. Significance and Implications], and [END of 8. Significance and Implications]).

Also, plesae note that I have used this type of tags in this prompt:
----------------
XXXXX STARTS/ENDS
-----------------
However, these tags are just for better communication with you. So, please do not include similar tags in your output.

Now, my draft is as follows. Please output only your revised introduction, without including any comments. Also, please return as a code block (``` tex\nYOUR REVISED ABSTRACT```).

-----------------
MY DRAFT STARTS
-----------------
PLACEHOLDER
-----------------
MY DRAFT ENDS
-----------------
