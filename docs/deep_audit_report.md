# Deep Audit Report — AI-Assisted Math on arXiv

- Generated: `2026-08-04T10:18:53+00:00`
- Model: `deepseek-v4-flash`
- Input (after first refine): **228** → confirmed **226**, demoted **2**
- Open-problem linked: **72**

## 1. How AI is used (primary role)

- **method_system_benchmark**: 100
- **proof_generation**: 71
- **exploration_search**: 23
- **formalization**: 13
- **counterexample_search**: 11
- **conjecture_discovery**: 7
- **code_numerics**: 1

### Multi-label AI roles

- method_system_benchmark: 116
- proof_generation: 90
- exploration_search: 56
- verification_check: 43
- formalization: 33
- conjecture_discovery: 25
- code_numerics: 22
- counterexample_search: 15
- writing_only: 5

## 2. AI centrality & human–AI relation

### Centrality
- **core**: 185
- **substantial**: 36
- **peripheral**: 5

### Relation
- **joint**: 98
- **human_led_ai_assist**: 32
- **ai_led**: 73
- **ai_method_only**: 23

## 3. Math subfields

- **optimization**: 76
- **cs_theory_adjacent**: 63
- **combinatorics**: 55
- **probability_stats**: 40
- **general_or_multiple**: 39
- **analysis**: 33
- **number_theory**: 27
- **mathematical_physics**: 16
- **logic_foundations**: 16
- **algebraic_geometry**: 14
- **algebra**: 12
- **discrete_geometry**: 10
- **dynamical_systems**: 10
- **graph_theory**: 8
- **other**: 5
- **topology_geometry**: 5
- **group_theory**: 1

## 4. Result / proof morphology

### Result type
- **open_problem_resolution**: 34
- **method_or_system**: 80
- **new_theorem**: 59
- **formalization_of_known_result**: 5
- **benchmark_evaluation**: 24
- **improved_bound_construction**: 10
- **counterexample**: 1
- **survey_position**: 12
- **other**: 1

### Proof style (multi)
- computer_assisted_search: 82
- none_or_na: 73
- research_level_argument: 72
- formal_machine_checked: 33
- informal_natural_language: 33
- constructive_example: 29

## 5. Formal systems & models mentioned

### Formal systems
- none: 192
- lean4: 28
- lean: 5
- isabelle: 1

### Models / systems
- chatgpt: 43
- claude: 11
- alphaevolve: 10
- gpt-4: 9
- gemini: 8
- gpt-5: 8
- aristotle: 5
- gpt-5.5: 5
- rethlas: 5
- gpt-5.6: 4
- gpt-5.5 pro: 3
- danus: 3
- llm: 3
- gpt-5.2: 2
- gpt-5.6 sol: 2
- gpt-5.6 pro: 2
- gpt-5.2 pro: 2
- grok: 2
- openai codex: 2
- t5: 2

## 6. Yearly volume (confirmed)

- **2022**: 1
- **2023**: 11
- **2024**: 16
- **2025**: 58
- **2026**: 140

## 7. Open problems / notable targets (sample)

- [2606.29687](https://arxiv.org/abs/2606.29687) — FGG conjecture  
  A Machine-Verified Proof of a Quantum-Optimization Conjecture
- [2510.23513](https://arxiv.org/abs/2510.23513) — Point convergence of Nesterov's accelerated gradient method  
  Point Convergence of Nesterov's Accelerated Gradient Method: An AI-Assisted Proof
- [2510.19804](https://arxiv.org/abs/2510.19804) — Erdős conjecture on Sidon sets and perfect difference sets  
  Forbidden Sidon subsets of perfect difference sets, featuring a human-assisted proof
- [2511.02864](https://arxiv.org/abs/2511.02864) — various open problems  
  Mathematical exploration and discovery at scale
- [2606.15159](https://arxiv.org/abs/2606.15159) — Erdős-Graham conjecture  
  Every natural number is a sum of distinct semiprime unit fractions
- [2601.07421](https://arxiv.org/abs/2601.07421) — Erdős Problem #728  
  Resolution of Erdős Problem #728: a writeup of Aristotle's Lean proof
- [2606.22636](https://arxiv.org/abs/2606.22636) — Kannan-Tetali-Vempala conjecture  
  Spectral Gap for the Binary Fixed-Margin Swap Chain
- [2511.12665](https://arxiv.org/abs/2511.12665) — Convergence of Nesterov's accelerated gradient method  
  The iterates of FISTA converge even under inexact computations and stochastic gradients
- [2605.29151](https://arxiv.org/abs/2605.29151) — Aluffi-Chen-Marcolli conjecture  
  Real-rootedness of the Poincaré polynomials of $\overline{\mathcal M}_{0,n}$: an AI-assisted proof
- [2510.20013](https://arxiv.org/abs/2510.20013) — Non-Interactive Correlation Distillation (NICD) with erasures  
  Counterexample to majority optimality in NICD with erasures
- [2605.08033](https://arxiv.org/abs/2605.08033) — Escobar-Klein-Weigandt conjecture  
  Weak Order on the MacNeille Completion of Bruhat Order
- [2607.22580](https://arxiv.org/abs/2607.22580) — Lin-Kumar threshold policy generalization  
  Optimality of a Threshold Policy for a Queueing System with One Fast Server and Two Identical Slow Servers
- [2607.20525](https://arxiv.org/abs/2607.20525) — Erdős–Szemerédi sum-product conjecture  
  Autonomous disproofs of the sum-product conjecture over $\mathbb R$ with GPT-5.5 Pro
- [2606.16738](https://arxiv.org/abs/2606.16738) — Elekes–Rónyai expander conjecture  
  A counterexample to the near-quadratic Elekes--Rónyai expander conjecture over $\mathbb R$
- [2603.28636](https://arxiv.org/abs/2603.28636) — Erdős problem on matching integers to distinct multiples  
  Optimal bounds for an Erdős problem on matching integers to distinct multiples
- [2605.11656](https://arxiv.org/abs/2605.11656) — Gaussian completely monotone conjecture  
  A Counterexample to the Gaussian Completely Monotone Conjecture
- [2607.04891](https://arxiv.org/abs/2607.04891) — Moraga's conjecture on rank bound for abelian p-group actions  
  A counterexample to the odd-dimensional rank bound for abelian \texorpdfstring{$p$}{p}-group actions
- [2608.01040](https://arxiv.org/abs/2608.01040) — Ehrhart's volume conjecture  
  The equality case of Ehrhart's volume conjecture
- [2608.02327](https://arxiv.org/abs/2608.02327) — Connes' rigidity conjecture  
  ICC property(T) groups without W$^*$-superrigidity
- [2605.00301](https://arxiv.org/abs/2605.00301) — Erdős Primitive Set Conjecture  
  Primitive sets and von Mangoldt chains: Erdős Problem #1196 and beyond
- [2605.19979](https://arxiv.org/abs/2605.19979) — Conjectures of Defant et al., Hopkins, and Sagan-Wilson  
  Short Proofs in Algebraic and Enumerative Combinatorics
- [2605.24160](https://arxiv.org/abs/2605.24160) — Crandall's problem on binary digits of Erdős-Borwein constant  
  On the binary digits of the Erdős-Borwein constant
- [2607.12208](https://arxiv.org/abs/2607.12208) — FDR control conjecture for correlated Gaussian tests  
  The Benjamini--Hochberg Procedure Can Fail to Control the FDR for Correlated Two-Sided Gaussian Tests
- [2604.27989](https://arxiv.org/abs/2604.27989) — Garamvölgyi-Jackson-Jordán conjecture  
  Cliques in minimally globally rigid graphs
- [2607.24528](https://arxiv.org/abs/2607.24528) — Feige's conjecture  
  On Feige's conjecture

## 8. Second-pass demotions (sample)

- `2604.05984`: No AI used; pure Lean formalization. Autoformalization only mentioned as future potential.  
  _Formalization of De Giorgi--Nash--Moser Theory in Lean_
- `2407.12674`: Computer-assisted proof with interval arithmetic, no explicit AI/LLM involvement; classical formal/computer-assisted method.  
  _Sharp isoperimetric inequalities on the Hamming cube near the critical exponent_

## 9. Trend reading (auto sketch)

Confirmed volume moves from **1** (2022) to **140** (2026). Dominant AI usage is **method_system_benchmark**; densest subfield signal is **optimization**; most common result type is **method_or_system**. Open-problem-linked papers: **72**. Multi-role counts show whether formalization co-occurs with proof generation—see `by_ai_roles_multi` in `deep_audit_summary.json`.

---

Method note: labels come from title/abstract via DeepSeek V4 Flash; not full-PDF verification. Treat as a structured proxy for local exploration.