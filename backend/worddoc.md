# Catalyst Backend – Prompt & Evaluation Documentation

## 1. Case-Study Generation Prompts

### 1.1 Multi-Part Case-Study Generation (`/api/generate-multipart-case`)
[This is the prompt that is used to generate the case study for the multi-part assessment.]
```
You are a senior manufacturing process expert. Create a realistic, complex manufacturing case study that will challenge problem-solving skills across multiple dimensions.

Write a case study (200-250 words) about a significant operational problem in a modern manufacturing facility.

The problem should involve multiple interconnected issues such as:
- Quality defects with unclear root causes
- Production inefficiencies or bottlenecks
- Equipment reliability issues
- Process control problems
- Supply chain or material issues
- Worker safety or ergonomic concerns
- Cost overruns or waste

Requirements:
- Start with "Case Study: [Descriptive Title]"
- Include specific, realistic data (percentages, quantities, timeframes, costs)
- Mention multiple departments/stakeholders affected
- Include both immediate symptoms and underlying issues
- Provide enough complexity to support 4-part analysis (data gathering, root cause analysis, solution development, implementation)
- Do NOT include any solutions or hints about causes
- End with "Your task is to analyze this problem systematically through a structured approach."

Make it realistic for a mid-to-large manufacturing operation with modern equipment and processes.
```

---

## 2. Evaluation Framework (Questions & Rubrics)
The assessment is divided into four parts. Each part contains three open-ended questions and a set of rubric criteria (used later by the AI evaluator).

### Part 1 – Problem Identification & Data Gathering
**Questions**
1. `q1_data` – What specific quantitative data would you collect to better understand this manufacturing problem? List 4-5 key metrics and explain why each is important.
2. `q1_stakeholders` – Who are the key people you would interview to gather information about this issue? For each person/role, specify what unique insights they could provide.
3. `q1_observations` – What direct observations would you make on the production floor? Describe your observation plan including timing, duration, and specific things to look for.

**Rubrics**
- `data_focus` – How well did they identify relevant quantitative metrics and explain their importance?
- `stakeholder_identification` – Did they identify appropriate people with clear rationale for what insights each could provide?
- `observation_skills` – How systematic and comprehensive is their observation plan?

Passing score (average): **5.0 / 10**

---

### Part 2 – Root Cause Analysis
**Questions**
1. `q2_causes` – Using a structured approach (like the 5M framework: Man, Machine, Material, Method, Environment), list 4-6 potential root causes for this problem. For each cause, explain your reasoning.
2. `q2_method` – What structured root cause analysis method would you use (e.g., 5 Whys, Fishbone Diagram, Fault Tree Analysis)? Explain your choice and how you would apply it to this specific problem.
3. `q2_validation` – How would you validate which root cause is the actual cause? Describe your testing/validation approach and what evidence you would look for.

**Rubrics**
- `systematic_thinking` – Did they use systematic frameworks and demonstrate structured thinking?
- `methodology` – Did they choose appropriate analysis methods and explain their reasoning?
- `validation_approach` – How well did they plan to test and validate their hypotheses?

Passing score (average): **5.0 / 10**

---

### Part 3 – Solution Development
**Questions**
1. `q3_solutions` – Propose 3-4 specific solutions that address the root causes you identified. For each solution, explain how it directly tackles the root cause and estimate the effort/cost level (Low/Medium/High).
2. `q3_implementation` – For your highest-priority solution, create a detailed implementation plan including: key steps, timeline, required resources, responsible parties, and success criteria.
3. `q3_risks` – What are the potential risks, challenges, or unintended consequences of your solution? For each risk, propose a mitigation strategy.

**Rubrics**
- `solution_relevance` – How directly and effectively do the solutions address the identified root causes?
- `practicality` – How realistic, detailed, and implementable are the solutions and plans?
- `risk_awareness` – Did they identify realistic risks and provide thoughtful mitigation strategies?

Passing score (average): **5.0 / 10**

---

### Part 4 – Implementation & Monitoring
**Questions**
1. `q4_metrics` – What specific KPIs and metrics would you track to measure if your solution is working? Include leading indicators (early signals) and lagging indicators (final results).
2. `q4_timeline` – Create a realistic timeline showing: implementation phases, when you expect to see initial improvements, when to measure full impact, and review checkpoints. Justify your timeframes.
3. `q4_sustainability` – How would you ensure the solution is sustained long-term? Address: training needs, process standardization, accountability measures, and continuous improvement mechanisms.

**Rubrics**
- `measurement_focus` – Did they identify appropriate leading and lagging indicators for success?
- `realistic_timeline` – Is their timeline realistic with proper justification for timeframes?
- `sustainability` – How well did they address long-term sustainability and continuous improvement?

Passing score (average): **5.0 / 10**

---

## 3. Part-Level Evaluation Prompt Template (`/api/submit-part`)
[This is the prompt that is used to evaluate the student's responses to the questions in the part.]
The backend builds the following prompt (placeholders in **bold** will be replaced at runtime):
```
You are an expert Operational Excellence consultant with 20+ years of experience evaluating manufacturing problem-solving capabilities.

EVALUATION CONTEXT:
Part **{partId}**: **{part.title}**

ORIGINAL CASE STUDY:
{case_study}

STUDENT RESPONSES:
{responses_text}

EVALUATION CRITERIA (Score 1-10 for each):
{rubrics_text}

EVALUATION INSTRUCTIONS:
0. If the student has provided no or irrelevant responses, score 1 and don't provide any feedback.
1. Score each criterion on a 1-10 scale where:
   - 1-3: Poor (lacks understanding, minimal effort, unrealistic)
   - 4-5: Below Average (basic understanding, limited depth)
   - 6-7: Good (solid understanding, practical approach)
   - 8-9: Excellent (comprehensive, insightful, well-structured)
   - 10: Outstanding (exceptional insight, innovative thinking)

2. Consider:
   - Depth and quality of responses
   - Practical applicability to manufacturing
   - Use of structured thinking approaches
   - Specificity and detail level
   - Realistic understanding of manufacturing operations

3. Student can proceed if average score ≥ **{part.passingScore}**

4. Provide constructive feedback (2-3 sentences) that:
   - Highlights specific strengths
   - Identifies specific areas for improvement
   - Offers actionable suggestions

   MAKE SURE THE CRITERIA ARE LABELLED EXACTLY AS THEY ARE IN THE PROMPT. DO NOT MAKE ANY CHANGES TO THE CRITERIA NAME INCLUDING REMOVING THE DASHES.
Format as JSON:
{
    "scores": {"criterion1": score, "criterion2": score, ...},
    "feedback": "detailed constructive feedback"
}

Respond only with valid JSON, no additional text.
```

---

## 4. Final Comprehensive Evaluation Prompt Template (`/api/final-evaluation/{session_id}`)
[This is the prompt that is used to evaluate the student's overall performance across all parts.]
```
You are a senior manufacturing consultant providing a comprehensive evaluation of problem-solving capabilities.

EVALUATION SUMMARY:
- Total Questions Answered: {session.total_questions}
- Overall Average Score: {overall_average}/10
- All Parts Completed Successfully

ORIGINAL CASE STUDY:
{session.case_study}

COMPLETE STUDENT RESPONSES:
{all_responses}

DETAILED PART EVALUATIONS:
{json.dumps(all_evaluations, indent=2)}

COMPREHENSIVE FINAL EVALUATION REQUIRED:

1. Overall Performance Scores (1-10):
   - analytical_thinking: Data gathering, systematic analysis, structured approaches
   - problem_solving: Root cause identification, solution development, creativity
   - systematic_approach: Use of frameworks, methodical thinking, logical flow
   - practical_application: Real-world feasibility, manufacturing knowledge, implementation focus

2. Performance Rating based on overall average:
   - "Excellent" (8.0+): Exceptional manufacturing problem-solving skills
   - "Good" (6.5-7.9): Strong competencies with minor gaps
   - "Satisfactory" (5.0-6.4): Adequate skills, needs development
   - "Needs Improvement" (<5.0): Significant skills gaps

3. Detailed Feedback (4-5 sentences):
   - Specific strengths demonstrated across all parts
   - Key areas for improvement with actionable recommendations
   - Overall assessment of manufacturing problem-solving maturity
   - Suggestions for continued development

Provide realistic, constructive evaluation that accurately reflects demonstrated capabilities.

Format as JSON:
{
    "overallScores": {
        "analytical_thinking": score,
        "problem_solving": score,
        "systematic_approach": score,
        "practical_application": score
    },
    "detailedFeedback": "comprehensive feedback paragraph",
    "overallPerformance": "performance rating"
}

Respond only with valid JSON.
```
