RUBRICS = {
    "usefulness": {
        "dimension": "usefulness",
        "question": "How useful is this skill for a developer who needs the capability it describes? Does it solve a real problem and provide actionable guidance?",
        "scale": {
            1: "Not useful — addresses no real need or provides no actionable guidance.",
            2: "Slightly useful — touches a real need but too vague or incomplete to act on.",
            3: "Moderately useful — addresses a real need with some actionable steps, but missing key details.",
            4: "Very useful — clearly addresses a real need with actionable, well-structured guidance.",
            5: "Extremely useful — solves a clear problem end-to-end with concrete, immediately actionable steps.",
        },
    },
    "efficiency": {
        "dimension": "efficiency",
        "question": "Is the skill concise and well-structured? Does it avoid unnecessary boilerplate, redundancy, and filler while still being complete?",
        "scale": {
            1: "Very inefficient — excessive boilerplate, redundancy, or filler that buries the useful content.",
            2: "Inefficient — notable padding or repetition; could be significantly shorter without losing value.",
            3: "Adequate — some unnecessary content but mostly focused; minor trimming possible.",
            4: "Efficient — concise and well-organized with minimal waste.",
            5: "Highly efficient — every section earns its place; dense with useful information, no filler.",
        },
    },
    "correctness": {
        "dimension": "correctness",
        "question": "Are the technical instructions, code examples, CLI commands, and configurations accurate? Would following them produce the expected results?",
        "scale": {
            1: "Incorrect — major errors that would cause failures if followed (wrong APIs, broken commands, invalid configs).",
            2: "Mostly incorrect — several significant errors mixed with some correct content.",
            3: "Partially correct — core approach is right but contains notable errors in details or examples.",
            4: "Mostly correct — minor issues that a developer could easily fix; overall approach and examples work.",
            5: "Fully correct — all instructions, code, commands, and configs are accurate and would work as written.",
        },
    },
    "safety": {
        "dimension": "safety",
        "question": "Does the skill follow security best practices? Does it avoid dangerous patterns (command injection, overly permissive IAM, unvalidated inputs, secrets in code) and include appropriate guardrails?",
        "scale": {
            1: "Unsafe — contains dangerous patterns with no guardrails (e.g., unquoted shell vars, wildcard IAM, eval of user input).",
            2: "Mostly unsafe — some security awareness but critical gaps remain.",
            3: "Partially safe — addresses some security concerns but misses important ones.",
            4: "Mostly safe — good security practices with minor gaps or missing edge cases.",
            5: "Very safe — comprehensive security guardrails, input validation, least-privilege IAM, and explicit safety instructions.",
        },
    },
    "completeness": {
        "dimension": "completeness",
        "question": "Does the skill cover the full workflow it describes? Are prerequisites, steps, edge cases, error handling, and gotchas addressed?",
        "scale": {
            1: "Incomplete — covers only a fragment of the workflow; missing critical steps.",
            2: "Mostly incomplete — covers the happy path but skips prerequisites, error handling, or important steps.",
            3: "Partially complete — covers the main workflow but missing edge cases, gotchas, or some steps.",
            4: "Mostly complete — covers the full workflow with minor gaps in edge cases or advanced scenarios.",
            5: "Fully complete — end-to-end coverage including prerequisites, all steps, edge cases, gotchas, and iteration guidance.",
        },
    },
}
