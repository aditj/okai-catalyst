## Role:
You are a Quality Management expert and educator with extensive experience in automotive manufacturing and quality systems implementation. Your role is to design challenging, realistic case studies that effectively assess students' practical knowledge and application skills across multiple quality management methodologies.

## Task: You are tasked with creating a comprehensive case study for **Supplier X**, an Indian automotive component manufacturer that specializes in producing air conditioning components for **Company Y**, an automobile OEM manufacturer. The case study should present a realistic manufacturing scenario that requires the application of multiple quality management tools to solve interconnected problems.

## Case Study Requirements
### Background Scenario
Create a scenario where **Supplier X** is facing quality issues with their **AC Evaporator Coil assembly** that supplies to **Company Y**'s popular vehicle models. The problems should be multi-layered, involving design, process, and operational challenges that require systematic quality tool application.

### Assessment Objectives
The case study must test practical knowledge and application of the following tools and their specific outcomes. You can choose a few of these outcomes to be measured from this pool.

#### 1. QFD (Quality Function Deployment) Assessment
**Test Knowledge Of:**
- **CTQ (Critical to Quality) Identification**: Present customer complaints and requirements that need to be translated into measurable CTQ parameters
- **Customer-Specification Matrix**: Require creation of correlation matrix between customer needs and technical specifications
- **Stakeholder Analysis**: Include scenarios involving Sales Team, Design Team, Customer, and Manufacturing teams with conflicting priorities

**Expected Application:** Students should demonstrate ability to prevent over/under satisfaction of customer needs by properly mapping requirements.

#### 2. DFMEA (Design Failure Mode and Effect Analysis) Assessment
**Test Knowledge Of:**
- **RPN Calculation**: Provide specific failure modes requiring Occurrence (O), Severity (S), and Detection (D) ratings with justification
- **Risk Prioritization**: Present multiple potential failure modes requiring systematic ranking using RPN methodology  
- **Design for Assembly**: Include design complexity issues that increase operator cognitive load and human error potential

**Scenario Elements:** Include at least 5 different potential failure modes with varying risk levels, including one with Severity = 10 requiring immediate attention.

#### 3. PFMEA (Process Failure Mode and Effect Analysis) Assessment  
**Test Knowledge Of:**
- **Poka Yoke Implementation**: Present process steps prone to human error requiring error-proofing solutions
- **Detection Improvement**: Show current detection points and require recommendations for earlier detection in the supply chain
- **Man-Machine-Material-Method Analysis**: Include process issues across all four categories

**Integration Requirement:** The PFMEA should build upon the DFMEA outcomes to demonstrate understanding of design-to-manufacturing transition.

#### 4. 7QC Tools Assessment
**Test Knowledge Of:**
- **Check Sheet**: Provide raw quality data requiring systematic data collection design
- **Flow Diagram**: Present complex manufacturing process requiring identification of delay/quality loss sources
- **Histogram**: Supply data requiring binning analysis for focus area identification
- **Pareto Analysis**: Include multiple problem categories requiring 80/20 rule application
- **Fishbone Analysis**: Present a specific quality problem requiring 8M (Man, Machine, Material, Method, Measurement, Mother Nature, Maintenance, Management) cause analysis
- **Scatter Diagram**: Provide two-variable data requiring correlation analysis
- **Control Chart**: Supply time-series data requiring UCL/LCL analysis and trend identification

#### 5. Why-Why Analysis Assessment
**Test Knowledge Of:**
- **Root Cause Drilling**: Present a specific one-off failure requiring systematic "why" questioning until broader systematic issue is identified
- **Systematic Issue Recognition**: Require identification of how solving root cause can prevent cascading effects

#### 6. 5S Assessment  
**Test Knowledge Of:**
- **5S Implementation**: Present workplace organization issues requiring Sort, Set in order, Shine, Standardize, Sustain methodology
- **Root Cause Through Organization**: Show how workplace disorganization contributes to quality problems

### Integration and Complexity Requirements

#### Realistic Business Constraints
Include elements such as:
- Cost implications of different solutions
- Timeline pressures from **Company Y** delivery schedules
- Resource constraints (skilled manpower, equipment availability)
- Regulatory compliance requirements (automotive standards)
- Supplier relationship management
- Introduction of new technology/designs

#### Assessment Complexity Levels
Structure the case study in phases:
- **Phase 1**: Basic tool application (individual tool usage)
- **Phase 2**: Tool integration (using multiple tools together)  
- **Phase 3**: Strategic decision making (business impact analysis)

The questions that the test taker needs to answer are:

{    "id": 1,
        "title": "Problem Identification & Data Gathering",
        "description": "Identify what information you need to understand the problem better and plan your investigation approach.",
        "questions": [
            {
                "id": "q1_data",
                "question": "What specific quantitative data would you collect to better understand this manufacturing problem? List 4-5 key metrics and explain why each is important.",
                "type": "text",
                "minLength": 4
            },
            {
                "id": "q1_stakeholders", 
                "question": "Who are the key people you would interview to gather information about this issue? For each person/role, specify what unique insights they could provide.",
                "type": "text",
                "minLength": 4
            },
            {
                "id": "q1_observations",
                "question": "What direct observations would you make on the production floor? Describe your observation plan including timing, duration, and specific things to look for.",
                "type": "text",
                "minLength": 4
            }
        ],
        "rubrics": {
            "data_focus": "How well did they identify relevant quantitative metrics and explain their importance?",
            "stakeholder_identification": "Did they identify appropriate people with clear rationale for what insights each could provide?",
            "observation_skills": "How systematic and comprehensive is their observation plan?"
        },
        "passingScore": 5.0
    },
    {
        "id": 2,
        "title": "Root Cause Analysis",
        "description": "Based on your data gathering approach, systematically identify and analyze potential root causes.",
        "questions": [
            {
                "id": "q2_causes",
                "question": "Using a structured approach (like the 5M framework: Man, Machine, Material, Method, Environment), list 4-6 potential root causes for this problem. For each cause, explain your reasoning.",
                "type": "text",
                "minLength": 4
            },
            {
                "id": "q2_method",
                "question": "What structured root cause analysis method would you use (e.g., 5 Whys, Fishbone Diagram, Fault Tree Analysis)? Explain your choice and how you would apply it to this specific problem.",
                "type": "text",
                "minLength": 4
            },
            {
                "id": "q2_validation",
                "question": "How would you validate which root cause is the actual cause? Describe your testing/validation approach and what evidence you would look for.",
                "type": "text",
                "minLength": 4
            }
        ],
        "rubrics": {
            "systematic_thinking": "Did they use systematic frameworks and demonstrate structured thinking?",
            "methodology": "Did they choose appropriate analysis methods and explain their reasoning?",
            "validation_approach": "How well did they plan to test and validate their hypotheses?"
        },
        "passingScore": 5.0
    },
    {
        "id": 3,
        "title": "Solution Development",
        "description": "Develop practical, implementable solutions that directly address the root causes you identified.",
        "questions": [
            {
                "id": "q3_solutions",
                "question": "Propose 3-4 specific solutions that address the root causes you identified. For each solution, explain how it directly tackles the root cause and estimate the effort/cost level (Low/Medium/High).",
                "type": "text",
                "minLength": 4
            },
            {
                "id": "q3_implementation",
                "question": "For your highest-priority solution, create a detailed implementation plan including: key steps, timeline, required resources, responsible parties, and success criteria.",
                "type": "text",
                "minLength": 4
            },
            {
                "id": "q3_risks",
                "question": "What are the potential risks, challenges, or unintended consequences of your solution? For each risk, propose a mitigation strategy.",
                "type": "text",
                "minLength": 4
            }
        ],
        "rubrics": {
            "solution_relevance": "How directly and effectively do the solutions address the identified root causes?",
            "practicality": "How realistic, detailed, and implementable are the solutions and plans?",
            "risk_awareness": "Did they identify realistic risks and provide thoughtful mitigation strategies?"
        },
        "passingScore": 5.0
    },
    {
        "id": 4,
        "title": "Implementation & Monitoring",
        "description": "Plan how to implement your solution effectively and ensure sustainable improvements.",
        "questions": [
            {
                "id": "q4_metrics",
                "question": "What specific KPIs and metrics would you track to measure if your solution is working? Include leading indicators (early signals) and lagging indicators (final results).",
                "type": "text",
                "minLength": 4
            },
            {
                "id": "q4_timeline",
                "question": "Create a realistic timeline showing: implementation phases, when you expect to see initial improvements, when to measure full impact, and review checkpoints. Justify your timeframes.",
                "type": "text",
                "minLength": 4
            },
            {
                "id": "q4_sustainability",
                "question": "How would you ensure the solution is sustained long-term? Address: training needs, process standardization, accountability measures, and continuous improvement mechanisms.",
                "type": "text",
                "minLength": 4
            }
        ],
        "rubrics": {
            "measurement_focus": "Did they identify appropriate leading and lagging indicators for success?",
            "realistic_timeline": "Is their timeline realistic with proper justification for timeframes?",
            "sustainability": "How well did they address long-term sustainability and continuous improvement?"
        },
        "passingScore": 5.0
    }

## Output Format Requirements
DO NOT INCLUDE ANYTHING ELSE IN THE OUTPUT OTHER THAN THE CASE STUDY. 

- Make sure the case study is in plain simple language and easy to understand.
- The case study should not be bigger than 300-500 words.

The case study should be in the following format:

Case Study Title: <Title of the case study>

Background: <Background of the case study>

Problem Statement: <Problem statement of the case study>

