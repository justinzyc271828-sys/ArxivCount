# Full-Text DeepSeek Audit Report

- Generated: `2026-08-04T11:24:25+00:00`
- Model: `deepseek-v4-flash`
- Input: **226** | download OK: **226**
- Confirmed after full text: **226** | demoted: **0**
- Keep→drop flips: **0** | role changes: **3**
- Writing-only demotions: **0**
- Open-problem linked: **86**

## Stance / method

Full text (PDF/HTML extract, head+tail) is more reliable than abstract-only for:
- distinguishing **writing help** vs **proof contribution**
- finding AI mentions in **acknowledgements / methods / appendices**
- refining **subfield** from actual mathematical content

Remaining limits: OCR/extraction errors; truncated middles; undisclosed AI use still invisible.

## 1. AI usage (primary role)

- **method_system_benchmark**: 100
- **proof_generation**: 73
- **exploration_search**: 23
- **formalization**: 12
- **counterexample_search**: 11
- **conjecture_discovery**: 6
- **code_numerics**: 1

### Multi-label roles

- method_system_benchmark: 113
- exploration_search: 93
- proof_generation: 87
- verification_check: 65
- code_numerics: 59
- formalization: 32
- writing_only: 26
- conjecture_discovery: 18
- counterexample_search: 14
- survey_position: 6
- benchmark_evaluation: 3
- literature_search: 1
- generalization: 1
- data_synthesis: 1
- evaluation: 1

## 2. Where AI is mentioned in the paper

- introduction: 209
- abstract: 197
- methods: 172
- results: 134
- acknowledgements: 109
- appendix: 96
- elsewhere: 31
- conclusion: 6
- footnote: 5
- discussion: 4
- not_found: 2
- remarks: 1
- conclusions: 1

## 3. Subfields

- **optimization**: 80
- **cs_theory_adjacent**: 72
- **combinatorics**: 61
- **probability_stats**: 41
- **general_or_multiple**: 41
- **analysis**: 38
- **number_theory**: 28
- **algebra**: 20
- **logic_foundations**: 20
- **mathematical_physics**: 18
- **algebraic_geometry**: 18
- **dynamical_systems**: 13
- **discrete_geometry**: 12
- **graph_theory**: 10
- **other**: 7
- **topology_geometry**: 6
- **group_theory**: 1
- **convex_geometry**: 1

## 4. Role × subfield (situation matrix)

- **optimization**: method_system_benchmark:54, proof_generation:12, exploration_search:10, formalization:1
- **combinatorics**: proof_generation:26, exploration_search:12, method_system_benchmark:8, formalization:4
- **cs_theory_adjacent**: method_system_benchmark:36, proof_generation:3, exploration_search:2, code_numerics:1
- **probability_stats**: proof_generation:18, method_system_benchmark:14, counterexample_search:4, exploration_search:1
- **analysis**: method_system_benchmark:13, proof_generation:11, counterexample_search:3, exploration_search:2
- **general_or_multiple**: method_system_benchmark:27, exploration_search:1
- **number_theory**: proof_generation:12, formalization:4, method_system_benchmark:4, exploration_search:4
- **mathematical_physics**: proof_generation:9, method_system_benchmark:4, formalization:2, exploration_search:2
- **algebra**: proof_generation:9, counterexample_search:3, method_system_benchmark:3, formalization:1
- **logic_foundations**: method_system_benchmark:10, formalization:5, proof_generation:1
- **algebraic_geometry**: proof_generation:10, counterexample_search:3, formalization:1, method_system_benchmark:1
- **dynamical_systems**: method_system_benchmark:7, exploration_search:3, proof_generation:1, counterexample_search:1
- **discrete_geometry**: proof_generation:3, exploration_search:3, counterexample_search:2, formalization:1
- **graph_theory**: proof_generation:6, exploration_search:3
- **topology_geometry**: proof_generation:3, formalization:1, method_system_benchmark:1, code_numerics:1

## 5. Result / proof morphology

- **open_problem_resolution**: 35
- **method_or_system**: 84
- **new_theorem**: 55
- **formalization_of_known_result**: 5
- **benchmark_evaluation**: 23
- **improved_bound_construction**: 10
- **other**: 2
- **counterexample**: 1
- **survey_position**: 11

### Proof style

- research_level_argument: 95
- computer_assisted_search: 84
- none_or_na: 71
- constructive_example: 48
- formal_machine_checked: 34
- informal_natural_language: 32
- probabilistic_method: 1

## 6. Yearly volume

- **2022**: 1
- **2023**: 11
- **2024**: 16
- **2025**: 58
- **2026**: 140

### Year × primary role

- **2022**: {'method_system_benchmark': 1}
- **2023**: {'method_system_benchmark': 9, 'proof_generation': 1, 'code_numerics': 1}
- **2024**: {'method_system_benchmark': 15, 'exploration_search': 1}
- **2025**: {'proof_generation': 11, 'formalization': 3, 'exploration_search': 10, 'counterexample_search': 1, 'method_system_benchmark': 32, 'conjecture_discovery': 1}
- **2026**: {'proof_generation': 61, 'formalization': 9, 'counterexample_search': 10, 'method_system_benchmark': 43, 'exploration_search': 12, 'conjecture_discovery': 5}

## 7. Models & formal systems

- chatgpt: 21
- gpt-4: 21
- gpt-4o: 19
- chatgpt 5.5 pro: 15
- gpt-5: 13
- deepseek-r1: 13
- gpt-5.5 pro: 12
- alphaevolve: 11
- gemini 2.5 pro: 10
- aristotle: 9
- rethlas: 8
- gpt-3.5: 8
- claude: 7
- claude code: 6
- danus: 6
- codex: 6
- gpt-5.2: 6
- llama: 6
- deepseek-v3: 6
- gpt-5.2 pro: 5

### Formal

- lean 4: 23
- lean: 16
- mathlib: 6
- sagemath: 2
- arb: 2
- lean 4.28.0: 2
- zfc: 2
- lean4: 1
- lean 4.32.1: 1
- arb interval arithmetic: 1

## 8. Open problems (sample)

- [2606.29687](https://arxiv.org/abs/2606.29687) — FGG conjecture  
  _A Machine-Verified Proof of a Quantum-Optimization Conjecture_  
  role=`proof_generation` sub=`['mathematical_physics', 'optimization', 'cs_theory_adjacent']`
- [2510.23513](https://arxiv.org/abs/2510.23513) — Point convergence of Nesterov's accelerated gradient method  
  _Point Convergence of Nesterov's Accelerated Gradient Method: An AI-Assisted Proof_  
  role=`proof_generation` sub=`['optimization', 'dynamical_systems']`
- [2510.19804](https://arxiv.org/abs/2510.19804) — Erdős's conjecture on extending Sidon sets to perfect difference sets (Problem #707)  
  _Forbidden Sidon subsets of perfect difference sets, featuring a human-assisted proof_  
  role=`formalization` sub=`['combinatorics', 'number_theory']`
- [2511.02864](https://arxiv.org/abs/2511.02864) — Various open problems including finite field Kakeya, autocorrelation inequalities, kissing numbers, etc.  
  _Mathematical exploration and discovery at scale_  
  role=`exploration_search` sub=`['analysis', 'combinatorics', 'number_theory']`
- [2606.15159](https://arxiv.org/abs/2606.15159) — Erdős–Graham problem on Egyptian fractions with restricted denominators (ω=2 case)  
  _Every natural number is a sum of distinct semiprime unit fractions_  
  role=`formalization` sub=`['number_theory', 'combinatorics']`
- [2601.07421](https://arxiv.org/abs/2601.07421) — Erdős Problem #728  
  _Resolution of Erdős Problem #728: a writeup of Aristotle's Lean proof_  
  role=`proof_generation` sub=`['number_theory', 'combinatorics']`
- [2606.22636](https://arxiv.org/abs/2606.22636) — KTV conjecture (Kannan-Tetali-Vempala) for binary fixed-margin swap chain  
  _Spectral Gap for the Binary Fixed-Margin Swap Chain_  
  role=`proof_generation` sub=`['probability_stats', 'combinatorics', 'cs_theory_adjacent']`
- [2511.12665](https://arxiv.org/abs/2511.12665) — Convergence of iterates of Nesterov's accelerated gradient method in the critical regime  
  _The iterates of FISTA converge even under inexact computations and stochastic gradients_  
  role=`proof_generation` sub=`['optimization']`
- [2605.29151](https://arxiv.org/abs/2605.29151) — Aluffi–Chen–Marcolli conjecture on real-rootedness of Poincaré polynomials of M_{0,n}  
  _Real-rootedness of the Poincaré polynomials of $\overline{\mathcal M}_{0,n}$: an AI-assisted proof_  
  role=`proof_generation` sub=`['algebraic_geometry', 'combinatorics']`
- [2510.20013](https://arxiv.org/abs/2510.20013) — Majority optimality in NICD with erasures  
  _Counterexample to majority optimality in NICD with erasures_  
  role=`counterexample_search` sub=`['probability_stats', 'combinatorics', 'cs_theory_adjacent']`
- [2605.08033](https://arxiv.org/abs/2605.08033) — Escobar–Klein–Weigandt conjecture on Cohen–Macaulay ASM varieties  
  _Weak Order on the MacNeille Completion of Bruhat Order_  
  role=`proof_generation` sub=`['combinatorics', 'algebra', 'algebraic_geometry']`
- [2607.22580](https://arxiv.org/abs/2607.22580) — Optimality of threshold policy for queueing system with one fast and two slow servers  
  _Optimality of a Threshold Policy for a Queueing System with One Fast Server and Two Identical Slow Servers_  
  role=`proof_generation` sub=`['optimization', 'probability_stats']`
- [2607.20525](https://arxiv.org/abs/2607.20525) — Erdős–Szemerédi sum-product conjecture over R  
  _Autonomous disproofs of the sum-product conjecture over $\mathbb R$ with GPT-5.5 Pro_  
  role=`proof_generation` sub=`['number_theory', 'combinatorics', 'algebra']`
- [2606.16738](https://arxiv.org/abs/2606.16738) — Near-quadratic Elekes–Rónyai expander conjecture over R  
  _A counterexample to the near-quadratic Elekes--Rónyai expander conjecture over $\mathbb R$_  
  role=`proof_generation` sub=`['number_theory', 'combinatorics', 'algebra']`
- [2603.28636](https://arxiv.org/abs/2603.28636) — Erdős Problem #650  
  _Optimal bounds for an Erdős problem on matching integers to distinct multiples_  
  role=`proof_generation` sub=`['combinatorics', 'number_theory']`
- [2605.11656](https://arxiv.org/abs/2605.11656) — Gaussian completely monotone conjecture  
  _A Counterexample to the Gaussian Completely Monotone Conjecture_  
  role=`counterexample_search` sub=`['probability_stats', 'analysis']`
- [2607.04891](https://arxiv.org/abs/2607.04891) — Moraga's conjecture on odd-dimensional rank bound for abelian p-group actions  
  _A counterexample to the odd-dimensional rank bound for abelian \texorpdfstring{$p$}{p}-group actions_  
  role=`counterexample_search` sub=`['algebraic_geometry', 'algebra']`
- [2608.01040](https://arxiv.org/abs/2608.01040) — Ehrhart's volume conjecture (equality case)  
  _The equality case of Ehrhart's volume conjecture_  
  role=`proof_generation` sub=`['combinatorics', 'discrete_geometry', 'number_theory']`
- [2608.02327](https://arxiv.org/abs/2608.02327) — Connes' rigidity conjecture for ICC property (T) groups  
  _ICC property(T) groups without W$^*$-superrigidity_  
  role=`counterexample_search` sub=`['algebra', 'dynamical_systems', 'general_or_multiple']`
- [2605.00301](https://arxiv.org/abs/2605.00301) — Erdős Problem #1196  
  _Primitive sets and von Mangoldt chains: Erdős Problem #1196 and beyond_  
  role=`proof_generation` sub=`['number_theory', 'combinatorics', 'probability_stats']`
- [2605.19979](https://arxiv.org/abs/2605.19979) — Conjectures of Defant et al., Hopkins, and Sagan and Wilson  
  _Short Proofs in Algebraic and Enumerative Combinatorics_  
  role=`proof_generation` sub=`['combinatorics', 'algebra']`
- [2605.24160](https://arxiv.org/abs/2605.24160) — Crandall's problem on the binary digits of the Erdős–Borwein constant  
  _On the binary digits of the Erdős-Borwein constant_  
  role=`proof_generation` sub=`['number_theory']`
- [2607.12208](https://arxiv.org/abs/2607.12208) — FDR control for correlated two-sided Gaussian tests  
  _The Benjamini--Hochberg Procedure Can Fail to Control the FDR for Correlated Two-Sided Gaussian Tests_  
  role=`proof_generation` sub=`['probability_stats']`
- [2604.27989](https://arxiv.org/abs/2604.27989) — Conjecture 6.3 by Garamvölgyi, Jackson, and Jordán  
  _Cliques in minimally globally rigid graphs_  
  role=`proof_generation` sub=`['graph_theory', 'combinatorics', 'discrete_geometry']`
- [2607.24528](https://arxiv.org/abs/2607.24528) — Feige's conjecture  
  _On Feige's conjecture_  
  role=`proof_generation` sub=`['probability_stats']`

## 9. Demoted after full text (sample)


## 10. Abstract vs full-text flips (sample)

- `2605.00301` keep True→True; role conjecture_discovery→proof_generation  
   | _Primitive sets and von Mangoldt chains: Erdős Problem #1196 and beyond_
- `2510.20728` keep True→True; role formalization→exploration_search  
   | _Co-Designing Quantum Codes with Transversal Diagonal Gates via Multi-Agent Systems_
- `2605.05192` keep True→True; role exploration_search→proof_generation  
   | _Almost-Orthogonality in Lp Spaces: A Case Study with Grok_

## 11. Bottom-line trend reading

Volume 2022:1 → 2026:140. After full-text review, dominant primary role is **method_system_benchmark**; densest subfield is **optimization**. Keep→drop flips: 0 (incl. writing-only 0). Open-problem-linked: 86. Use role×subfield matrix for situation-specific conclusions.

---
PDFs cached under `data/downloads/` (local only). Labels via DeepSeek V4 Flash full-text excerpts.