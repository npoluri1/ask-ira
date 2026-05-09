"""
Prompt templates for the Ask IRA multi-agent research workflow.

Each template is a Python format string that gets populated by the workflow nodes
with topic, research data, analysis, and report content at each stage.
"""

RESEARCH_TASK_TEMPLATE = """You are a financial research agent conducting research on:

Topic: {topic}

Research depth: {num_queries} parallel queries

Gather information on:
1. Company overview, business model, and competitive position
2. Financial performance (revenue, margins, growth trends)
3. Market sentiment and analyst consensus
4. Macroeconomic factors affecting the sector
5. Key risks and catalysts

Provide a comprehensive research summary with key findings, statistics,
expert opinions, and source credibility assessment.
"""

ANALYSIS_TASK_TEMPLATE = """You are a senior investment analyst synthesizing research on:

Topic: {topic}

Raw research data:
{research_data}

Produce a structured analysis with:
1. Executive Summary — thesis and key findings
2. Financial Health Assessment — margins, growth, cash flow, debt
3. Competitive Position — moat, market share, differentiation
4. Sentiment Analysis — market, analyst, and media sentiment
5. Macro Environment — relevant economic indicators and trends
6. Risk Assessment — key risks with probability/impact scoring
7. Confidence Rating — 0.0-1.0 score with justification
"""

WRITING_TASK_TEMPLATE = """You are a financial writer producing a professional research report on:

Topic: {topic}

Structured analysis:
{analysis_data}

Report requirements:
- {num_sections} main sections with markdown headings
- Approximately {target_words} words
- Executive summary at the top
- Data-driven analysis with specific metrics
- Clear investment thesis with supporting evidence
- Risk factors and mitigants section
- Final recommendation with confidence rating

Use professional tone suitable for institutional investors.
"""

REVIEW_TASK_TEMPLATE = """You are a quality assurance reviewer evaluating a research report on:

Topic: {topic}

Report to review:
{report_content}

Evaluate on these dimensions (score each 1-10):
1. Accuracy — are claims supported by data?
2. Completeness — are all key aspects covered?
3. Clarity — is the writing clear and well-structured?
4. Objectivity — is the analysis balanced and unbiased?
5. Actionability — does it provide clear investment guidance?

Format your response as:
Overall Score: X/10
Dimension Scores: [accuracy, completeness, clarity, objectivity, actionability]
Issues Found: [list with severity: Critical/Major/Minor]
Improvement Suggestions: [actionable items]
Approval Decision: Yes/No
"""
