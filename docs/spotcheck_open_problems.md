# Human Spot-Check Queue

Source: `fulltext_confirmed.jsonl` · top **25** by priority

Priority favors: open problems, proof/counterexample/formalization, ai_led, low model confidence, abstract↔fulltext flips, recent years.

Fill `human_verdict` with: `confirm` / `demote` / `unsure`.

| # | arXiv | Role | Open problem | Subfields | Action |
|---|-------|------|--------------|-----------|--------|
| 1 | [2601.07421](https://arxiv.org/abs/2601.07421) | `proof_generation` | Erdős Problem #728 | number_theory, combinatorics |  |

**Resolution of Erdős Problem #728: a writeup of Aristotle's Lean proof**

- Summary: AI system (GPT-5.2 + Aristotle) autonomously proved Erdős Problem #728 in Lean; paper provides informal writeup and further extensions.
- Relation: `ai_led` · centrality: `core` · conf: 0.95
- Evidence: ['The system in question is a combination of GPT-5.2 Pro by OpenAI and Aristotle by Harmonic, operated by Kevin Barreto.', 'The author has received substantial assistance from ChatGPT in writing this manuscript. Indeed, a large fraction of the words were penned by ChatGPT.', 'Boris Alexeev ran Aristotle to simplify the proof; Kevin Barreto produced the original proofs; KoishiChan performed literature search.', 'The following result was derived in a conversation with ChatGPT. It was drafted by ChatGPT and edited and checked by the author.']
- PDF: https://arxiv.org/pdf/2601.07421.pdf

---

| 2 | [2606.16738](https://arxiv.org/abs/2606.16738) | `proof_generation` | Near-quadratic Elekes–Rónyai expander conjecture over R | number_theory, combinatorics, algebra |  |

**A counterexample to the near-quadratic Elekes--Rónyai expander conjecture over $\mathbb R$**

- Summary: AI (ChatGPT 5.5 Pro and Rethlas) generated a counterexample disproving the near-quadratic Elekes–Rónyai expander conjecture over R, with a fixed nonspecial quadratic polynomial and algebraic integer sets.
- Relation: `ai_led` · centrality: `core` · conf: 0.95
- Evidence: ['The main result of this paper is obtained by generative AI, particularly ChatGPT 5.5 Pro and the Rethlas system.', 'ChatGPT 5.5 Pro suggested that the question might be tractable using the newly developed theory in [OAI26] and [BSSZ26], and recommended the test function f(x,y)=x^2+xy+y^2.', 'We then ran the Rethlas system on the question and obtained an answer within 45 minutes.', 'The proof was then organized as the algebraic-number-theoretic construction treated below and checked against the two signed lemmas used in Sections 3 and 4.']
- PDF: https://arxiv.org/pdf/2606.16738.pdf

---

| 3 | [2607.04891](https://arxiv.org/abs/2607.04891) | `counterexample_search` | Moraga's conjecture on odd-dimensional rank bound for abelian p-group actions | algebraic_geometry, algebra |  |

**A counterexample to the odd-dimensional rank bound for abelian \texorpdfstring{$p$}{p}-group actions**

- Summary: AI systems (ChatGPT 5.5 pro and Danus) produced a counterexample to Moraga's conjectured rank bound for abelian p-group actions on Calabi-Yau threefolds, using the Fermat quintic with a (Z/5Z)^4 action.
- Relation: `ai_led` · centrality: `core` · conf: 0.95
- Evidence: ['The main result of this paper was obtained by ChatGPT 5.5 pro', 'The sketch of the proof of the main result of this paper was obtained by Chatgpt 5.5 pro', 'and later summed up, verified, and properly written by the Danus system', 'Human verification and polishing were done afterwards.']
- PDF: https://arxiv.org/pdf/2607.04891.pdf

---

| 4 | [2606.10806](https://arxiv.org/abs/2606.10806) | `conjecture_discovery` | Neural Jacobian Conjecture (NJC) for N ≥ n+2 | algebra, analysis, cs_theory_adjacent |  |

**Moonshine: An Autonomous Mathematical Research Agent Centered on Conjecture Generation**

- Summary: Moonshine, an autonomous AI agent, formulates the Neural Jacobian Conjecture and uses LLMs to prove it for low-width cases, leaving higher-width open.
- Relation: `ai_led` · centrality: `core` · conf: 0.95
- Evidence: ['By invoking GPT-5.5-pro and DeepSeek-V4-pro separately, Moonshine obtained independent complete proofs for the case N=n+1.', 'The first proof below was obtained by Moonshine using GPT-5.5-pro.', 'The following second proof was obtained by Moonshine using DeepSeek-V4-pro.', 'The following geometric-topological proof was developed with the assistance of ChatGPT, using GPT-5.5-pro through interactive use of its web interface.']
- PDF: https://arxiv.org/pdf/2606.10806.pdf

---

| 5 | [2606.29593](https://arxiv.org/abs/2606.29593) | `proof_generation` | Worst-case last-iterate convergence of randomized Kaczmarz | optimization, cs_theory_adjacent, analysis |  |

**How AI settled the complexity of the oldest SGD algorithm**

- Summary: AI models Gemini and ChatGPT collaboratively proved the optimal O(1/epsilon) last-iterate convergence rate for the randomized Kaczmarz algorithm, resolving a long-standing open problem.
- Relation: `ai_led` · centrality: `core` · conf: 0.95
- Evidence: ['In what could be described as a full circle, the complexity of the oldest SGD algorithm was settled through a collaboration between Gemini Deep Think and ChatGPT Pro, which was only initiated and facilitated by the authors.', 'Gemini discovered a novel connection to a branch of functional analysis that was previously unfamiliar to the authors, which allowed ChatGPT to derive an elementary proof of the claim.', 'We posed this problem to ChatGPT Pro (versions 5.1 and 5.2, latest at the time), and after multiple rounds of discussion ... we obtained the following claim.', 'The detailed proof, which was rewritten for clarity but remains largely unchanged, is given in the following section.']
- PDF: https://arxiv.org/pdf/2606.29593.pdf

---

| 6 | [2608.01156](https://arxiv.org/abs/2608.01156) | `proof_generation` | Uniform Gromov–Hausdorff gap problem | topology_geometry, discrete_geometry |  |

**The Uniform Gromov Hausdorff Gap Problem for Approximating Spheres by Finite Homogeneous Spaces**

- Summary: ChatGPT proves a quantitative lower bound for the uniform Gromov-Hausdorff gap problem for approximating spheres by finite homogeneous spaces.
- Relation: `ai_led` · centrality: `core` · conf: 0.95
- Evidence: ['ChatGPT provided the proofs and wrote the paper.', 'ChatGPT combines the passage from small Gromov–Hausdorff error to an approximate finite action on the sphere, logarithmic stability of approximate inner-product-preserving maps due to Cuesta, operator-norm stability of almost representations, and Green’s width theorem for finite transitive sets.']
- PDF: https://arxiv.org/pdf/2608.01156.pdf

---

| 7 | [2607.00708](https://arxiv.org/abs/2607.00708) | `proof_generation` | Jin-Rubinstein Problem 1.2 | algebraic_geometry, analysis |  |

**An equivariant fixed-level Demailly identity for Fano manifolds**

- Summary: AI (ChatGPT 5.5 pro and Danus) proved the equality of fixed-level equivariant alpha invariant and global log canonical threshold for Fano manifolds, resolving an open problem.
- Relation: `ai_led` · centrality: `core` · conf: 0.95
- Evidence: ['The main result of this paper was obtained by Chatgpt 5.5 pro, and the Danus system based on the Rethlas system.', 'The sketch of the proof of the main result of this paper was obtained by Chatgpt 5.5 pro, and later summed up, verified, and properly written by the Danus system.', 'Human verification and polishing were done afterwards.', 'The authors would like to thank the Rethlas team ... for their contributions to the development of Rethlas and its customized version used for the problem studied in this paper.']
- PDF: https://arxiv.org/pdf/2607.00708.pdf

---

| 8 | [2605.19979](https://arxiv.org/abs/2605.19979) | `proof_generation` | Conjectures of Defant et al., Hopkins, and Sagan and Wilson | combinatorics, algebra |  |

**Short Proofs in Algebraic and Enumerative Combinatorics**

- Summary: ChatGPT 5.4 Pro autonomously produced proofs resolving several open conjectures in algebraic and enumerative combinatorics.
- Relation: `ai_led` · centrality: `core` · conf: 0.98
- Evidence: ['All of the proofs in this article were discovered autonomously by ChatGPT 5.4 Pro.', 'The main contributions of the author were to find the problems, digest and verify the proofs, polish the writing, and provide exposition about each of the topics.', 'The relevant ChatGPT conversations are included in an ancillary file here.', 'The author thanks Harvard University and OpenAI for providing access to ChatGPT 5.4 Pro.']
- PDF: https://arxiv.org/pdf/2605.19979.pdf

---

| 9 | [2512.10220](https://arxiv.org/abs/2512.10220) | `proof_generation` | Monotonicity of learning curves for MLE (Gaussian variance estimation) | probability_stats |  |

**On Learning-Curve Monotonicity for Maximum Likelihood Estimators**

- Summary: GPT-5.2 Pro derived proofs of learning-curve monotonicity for MLE in Gaussian and Gamma settings; humans verified.
- Relation: `ai_led` · centrality: `core` · conf: 0.95
- Evidence: ['All results in this paper were derived by variants of GPT-5.2 Pro.', 'The proof of Theorem 1.1, which directly addresses the question of [VML19], was originally due to an unreleased prototype of a longer-thinking-time version of GPT-5.2 Pro.', 'GPT-5.2 Pro subsequently generalized it further to higher dimensional Gaussians, unknown means, and Gamma variables.', 'In summary, the human contributions to this paper (aside from the development of GPT-5.2 Pro and its internal variant) were as follows: (a) Prompting the model to continue generalizing its results.']
- PDF: https://arxiv.org/pdf/2512.10220.pdf

---

| 10 | [2601.18005](https://arxiv.org/abs/2601.18005) | `exploration_search` | Sphere packing in hypercubes, Heilbronn triangle problem, circle packing with maximal sum of radii, star discrepancy minimization | discrete_geometry, optimization, combinatorics |  |

**Flow-based Extremal Mathematical Structure Discovery**

- Summary: FlowBoost uses flow-matching and reward optimization to discover extremal geometric structures, improving bounds on circle packing and other problems.
- Relation: `ai_led` · centrality: `core` · conf: 0.95
- Evidence: ['We introduce FlowBoost, a closed-loop generative framework that learns to discover rare and extremal combinatorial structures by combining three components: (i) a geometry-aware conditional flow-matching model...', 'Reward-guided policy optimization with action exploration that directly optimizes the generation process toward the objective while maintaining diversity.', 'In several cases, FlowBoost discovers configurations that match or exceed the best known results. For circle packings, we improve the best known lower bounds, surpassing the LLM-based system AlphaEvolve...', 'The code is available at https://github.com/berczig/FlowBoost.']
- PDF: https://arxiv.org/pdf/2601.18005.pdf

---

| 11 | [2606.15159](https://arxiv.org/abs/2606.15159) | `formalization` | Erdős–Graham problem on Egyptian fractions with restricted denominators (ω=2 case) | number_theory, combinatorics |  |

**Every natural number is a sum of distinct semiprime unit fractions**

- Summary: AI-assisted proof that every natural number is a sum of distinct semiprime unit fractions, formalized in Lean 4, resolving the ω=2 case of an Erdős–Graham conjecture.
- Relation: `human_led_ai_assist` · centrality: `core` · conf: 0.95
- Evidence: ['AI tools (notably Anthropic’s Claude, used through Claude Code) contributed substantially to the Lean formalisation, the experiments, and the writing', 'This work is a human–AI collaboration: AI tools ... contributed substantially to the Lean formalisation, the experiments, and the writing', 'AI assistants—principally Anthropic’s Claude, used through Claude Code, together with other frontier models used for exploratory discussion—contributed substantially to the Lean 4 / Mathlib formalisation, to the Python verification scripts, and to parts of the exposition.', 'Precisely because the development was AI-assisted, every theorem is machine-checked in Lean with no sorry']
- PDF: https://arxiv.org/pdf/2606.15159.pdf

---

| 12 | [2606.22636](https://arxiv.org/abs/2606.22636) | `proof_generation` | KTV conjecture (Kannan-Tetali-Vempala) for binary fixed-margin swap chain | probability_stats, combinatorics, cs_theory_adjacent |  |

**Spectral Gap for the Binary Fixed-Margin Swap Chain**

- Summary: AI-generated proof of the KTV conjecture for binary swap chains, formalized in Lean, with human guidance and verification.
- Relation: `human_led_ai_assist` · centrality: `core` · conf: 0.95
- Evidence: ['The proof itself was generated by ChatGPT 5.5 Pro.', 'ChatGPT proposed the whole proof strategy, including the comparison with the two-row heat-bath chain, the reduction to the three-row case, and the decomposition of the three-row function space into the count sector and the Johnson harmonic sectors.', 'It also generated all the technical lemmas and initial proofs.', "The author's role was to pose the problem, guide the search direction, evaluate the AI-generated arguments, rewrite the proof, and take responsibility for the final form and validity of the result."]
- PDF: https://arxiv.org/pdf/2606.22636.pdf

---

| 13 | [2605.29151](https://arxiv.org/abs/2605.29151) | `proof_generation` | Aluffi–Chen–Marcolli conjecture on real-rootedness of Poincaré polynomials of M_{0,n} | algebraic_geometry, combinatorics |  |

**Real-rootedness of the Poincaré polynomials of $\overline{\mathcal M}_{0,n}$: an AI-assisted proof**

- Summary: AI-assisted proof of real-rootedness of Poincaré polynomials of M_{0,n} via a bivariate deformation, with human verification and extension to Fulton-MacPherson spaces.
- Relation: `human_led_ai_assist` · centrality: `core` · conf: 0.95
- Evidence: ['The proof of the real-rootedness theorem for the Poincaré polynomials of M_{0,n} was obtained through an iterative AI-assisted workflow with Co-Mathematician, an agentic frontier-model system developed by Google DeepMind.', 'Our role was to formulate the problem, evaluate the proposed proof attempts, identify gaps and request corrections, compare the developing argument with the literature, and refine the presentation of the final proof.', 'The first workstream already found the key strategy of the proof. The problem was reformulated as an interlacing statement and the bivariate deformation F_m(y,t) was introduced.', 'In summary, in this work the Co-Mathematician system was useful for proposing a proof strategy, testing it in examples, producing algebraic manipulations, and iteratively improving mathematical rigour.']
- PDF: https://arxiv.org/pdf/2605.29151.pdf

---

| 14 | [2605.08033](https://arxiv.org/abs/2605.08033) | `proof_generation` | Escobar–Klein–Weigandt conjecture on Cohen–Macaulay ASM varieties | combinatorics, algebra, algebraic_geometry |  |

**Weak Order on the MacNeille Completion of Bruhat Order**

- Summary: ChatGPT 5.4 Pro autonomously proved a conjecture and found a counterexample in Coxeter group combinatorics, leading to new theorems on MacNeille completions and ASM varieties.
- Relation: `human_led_ai_assist` · centrality: `core` · conf: 0.95
- Evidence: ['The proof of the conjecture of Escobar–Klein–Weigandt and the disproof of the conjecture of Hamaker–Reiner were obtained autonomously by ChatGPT 5.4 Pro.', 'In Figure 1, we exhibit a counterexample to this conjecture, which we discovered using ChatGPT 5.4 Pro.', 'Our proof of Theorem 1.3 was obtained autonomously by ChatGPT 5.4 Pro.', 'In Section 6, we discuss the use of ChatGPT in producing this manuscript, especially for proving Theorem 1.3.']
- PDF: https://arxiv.org/pdf/2605.08033.pdf

---

| 15 | [2607.22580](https://arxiv.org/abs/2607.22580) | `proof_generation` | Optimality of threshold policy for queueing system with one fast and two slow servers | optimization, probability_stats |  |

**Optimality of a Threshold Policy for a Queueing System with One Fast Server and Two Identical Slow Servers**

- Summary: GPT-5.5 Pro generated proofs for optimal threshold policy in three-server queueing system; authors verified and formalized key lemmas in Lean 4.
- Relation: `human_led_ai_assist` · centrality: `core` · conf: 0.95
- Evidence: ['The core technical ideas in this paper are generated by GPT-5.5 Pro.', 'We have included a short report describing the authors’ interactions with GPT-5.5 Pro.', 'The authors verified the proofs and rewrote the paper for better rigor, clarity, and exposition.', 'Three key lemmas have also been verified in Lean 4.']
- PDF: https://arxiv.org/pdf/2607.22580.pdf

---

| 16 | [2607.20525](https://arxiv.org/abs/2607.20525) | `proof_generation` | Erdős–Szemerédi sum-product conjecture over R | number_theory, combinatorics, algebra |  |

**Autonomous disproofs of the sum-product conjecture over $\mathbb R$ with GPT-5.5 Pro**

- Summary: A simple agent built on GPT-5.5 Pro autonomously generated correct proofs that the sum-product conjecture is false over R in 7/8 trials, with human verification.
- Relation: `human_led_ai_assist` · centrality: `core` · conf: 0.95
- Evidence: ['The agent autonomously generated correct proofs that the sum-product conjecture is false over R in 7 of 8 independent trials', 'The system used an average of 132.4k reasoning tokens per trial', 'GPT-5.5 and GPT-5.5 Pro assisted the author in understanding the proofs generated by the agent', 'GPT-5.5 Codex assisted in preparing Table 1 from the reasoning-token data']
- PDF: https://arxiv.org/pdf/2607.20525.pdf

---

| 17 | [2605.11656](https://arxiv.org/abs/2605.11656) | `counterexample_search` | Gaussian completely monotone conjecture | probability_stats, analysis |  |

**A Counterexample to the Gaussian Completely Monotone Conjecture**

- Summary: GPT-5.5 Pro found an explicit probability measure disproving the Gaussian completely monotone conjecture, with rigorous verification via SageMath/Arb.
- Relation: `human_led_ai_assist` · centrality: `core` · conf: 0.95
- Evidence: ['The explicit counterexample was found by GPT-5.5 Pro.', 'The SageMath/Arb computation in Section A, using exact rational input data and 256-bit complex balls, proves ...', 'All integrations are carried out with Arb ball arithmetic [Joh17] through SageMath’s ComplexBallField.integral; the printed balls are rigorous enclosures.']
- PDF: https://arxiv.org/pdf/2605.11656.pdf

---

| 18 | [2608.01040](https://arxiv.org/abs/2608.01040) | `proof_generation` | Ehrhart's volume conjecture (equality case) | combinatorics, discrete_geometry, number_theory |  |

**The equality case of Ehrhart's volume conjecture**

- Summary: Generative AI (GPT-5.6-sol, Fable 5, Danus) proves the equality case of Ehrhart's volume conjecture, showing equality bodies are unimodular simplices.
- Relation: `human_led_ai_assist` · centrality: `core` · conf: 0.95
- Evidence: ['The main result of this paper is obtained by generative AI, particularly GPT-5.6-sol, Fable 5, and the Danus system.', 'This observation was given to the Danus system, which carried out the first half of the proof along the suggested correspondence, found the mechanisms of the second half, for which no correspondence was available, on its own, and produced the complete proof, internally verified by the system’s proof-checking pipeline, in 3 hours and 16 minutes.', 'Discussions with Fable 5 and GPT-5.6-sol-ultra also assisted the author in quickly grasping the methodology of the proof of [OAI26, Chapter 8, Theorem 1.1].', 'Human verification and polishing were done afterwards.']
- PDF: https://arxiv.org/pdf/2608.01040.pdf

---

| 19 | [2608.02327](https://arxiv.org/abs/2608.02327) | `counterexample_search` | Connes' rigidity conjecture for ICC property (T) groups | algebra, dynamical_systems, general_or_multiple |  |

**ICC property(T) groups without W$^*$-superrigidity**

- Summary: Explicit construction of two non-isomorphic ICC property (T) groups with isomorphic von Neumann algebras, disproving Connes' rigidity conjecture, with AI assistance.
- Relation: `human_led_ai_assist` · centrality: `core` · conf: 0.95
- Evidence: ['The construction underlying the main result of this paper was found mainly by GPT-5.6 Sol, Codex, and the Danus multi-agent research system [LGS+26], under the author’s mathematical guidance.', 'Lean 4.32.1 was used to formally check selected parts of the argument.', 'This result was obtained with assistance from GPT-5.6 Sol, independently of and concurrently with work by OpenAI [Ope26].', 'The present construction was developed with the assistance of GPT-5.6 Sol, and a preliminary proof manuscript had been assembled by July 27, 2026.']
- PDF: https://arxiv.org/pdf/2608.02327.pdf

---

| 20 | [2605.00301](https://arxiv.org/abs/2605.00301) | `proof_generation` | Erdős Problem #1196 | number_theory, combinatorics, probability_stats |  |

**Primitive sets and von Mangoldt chains: Erdős Problem #1196 and beyond**

- Summary: AI-generated Markov chain methods prove several Erdős conjectures on primitive sets, including #1196, #164, and #1217.
- Relation: `joint` · centrality: `core` · conf: 0.95
- Evidence: ['The initial proof of Theorem 1.1 was generated by an autonomous run of GPT-5.4 Pro; a similar run also established Theorem 1.6.', 'GPT-5.4 Pro was also used to assist with the initial proof of Theorem 1.2, with the main human contributions being the downward divisor chain and suggesting Lemmas 3.2 and 3.3(ii).', 'The Lean formalization in [2] was generated using OpenAI’s Codex. The Lean formalization in [33] was generated using Math Inc.’s Gauss.', 'ChatGPT was used to generate code for several of the images in this paper, to search for relevant literature, to proofread the paper and to offer additional suggested results and remarks.']
- PDF: https://arxiv.org/pdf/2605.00301.pdf

---

| 21 | [2607.12208](https://arxiv.org/abs/2607.12208) | `proof_generation` | FDR control for correlated two-sided Gaussian tests | probability_stats |  |

**The Benjamini--Hochberg Procedure Can Fail to Control the FDR for Correlated Two-Sided Gaussian Tests**

- Summary: GPT-5.6 Pro found a counterexample disproving a 20-year-old conjecture on FDR control for correlated two-sided Gaussian tests, verified with rigorous interval arithmetic.
- Relation: `human_led_ai_assist` · centrality: `core` · conf: 0.95
- Evidence: ['The proof was obtained by GPT-5.6 Pro.', 'The model was asked directly to prove or disprove the conjecture and was provided only with the mathematical definition of the Benjamini–Hochberg procedure.', 'After about 90 minutes of reasoning, the model produced a proof, an example, and code for the numerical certificate, which form the basis of this paper.', 'The author carefully checked the entire argument and the associated numerical certificate.']
- PDF: https://arxiv.org/pdf/2607.12208.pdf

---

| 22 | [2604.27989](https://arxiv.org/abs/2604.27989) | `proof_generation` | Conjecture 6.3 by Garamvölgyi, Jackson, and Jordán | graph_theory, combinatorics, discrete_geometry |  |

**Cliques in minimally globally rigid graphs**

- Summary: ChatGPT 5.5 generated a proof confirming a conjecture about minimally globally rigid graphs, with human verification and editing.
- Relation: `human_led_ai_assist` · centrality: `core` · conf: 0.95
- Evidence: ['The proof of Theorem 1.2 was generated by ChatGPT 5.5, accessed through a Plus subscription.', 'The model independently identified this strategy, and produced the subsequent proof.', 'The author then checked the proof and edited it for clarity and exposition.']
- PDF: https://arxiv.org/pdf/2604.27989.pdf

---

| 23 | [2607.26396](https://arxiv.org/abs/2607.26396) | `proof_generation` | Question of Ciliberto, Miranda, and Roé on the number of common flex lines in a general pencil of cubics | algebraic_geometry |  |

**Twelve common flex lines in a general pencil of cubics**

- Summary: AI (ChatGPT 5.5 Pro, Danus) helped prove that a general pencil of plane cubics has exactly 12 common flex lines, answering an open question.
- Relation: `human_led_ai_assist` · centrality: `core` · conf: 0.95
- Evidence: ['The main result of this paper was obtained using generative AI, particularly ChatGPT 5.5 Pro and the Danus system.', 'Human verification and polishing were done afterwards.', 'Due to the limitation of generative AI, it is possible that we have missed some related references in the literature.']
- PDF: https://arxiv.org/pdf/2607.26396.pdf

---

| 24 | [2607.23307](https://arxiv.org/abs/2607.23307) | `proof_generation` | Variance conjecture (thin-shell inequality) | probability_stats, analysis, other |  |

**Digesting the proof of the sharp thin-shell inequality**

- Summary: AI (GPT-5.6 Pro) found a proof of the sharp thin-shell inequality for log-concave distributions, determining the optimal constant 8.
- Relation: `human_led_ai_assist` · centrality: `core` · conf: 0.95
- Evidence: ['The proof was found by GPT-5.6 Pro in response to prompts supplied by the first-named author', 'Section 3 contains the 3rd-moment computations by GPT-5.6 Pro', 'GPT-5.6 was then used to polish the writing', 'AI use statement: GPT-5.6 Pro produced the initial proof']
- PDF: https://arxiv.org/pdf/2607.23307.pdf

---

| 25 | [2607.06693](https://arxiv.org/abs/2607.06693) | `proof_generation` | Conjecture by Calderbank–Daubechies–Freeman–Freeman on stable phase retrieval for independent random variables | analysis, probability_stats |  |

**Stable Phase Retrieval for Spans of Independent Random Variables**

- Summary: LLM-assisted proof and Lean formalization of a conjecture characterizing stable phase retrieval for spans of independent random variables.
- Relation: `human_led_ai_assist` · centrality: `core` · conf: 0.95
- Evidence: ['This latter proof was partially LLM generated based on the ideas in the first proof and a considerable amount of guidance by the authors.', 'A first key contribution of an LLM was the suggestion of the general principle that one may forego with the Gaussian nature of the limit and replace it with the fact that a nontrivial infinitely divisible random vector in R2 supported on the cross ...', 'Seeking an argument that was both explicitly quantitative and better suited to formal verification, we prompted LLMs for an alternative to the infinitely divisible proof. The resulting strategy – LLM-generated with significant human guidance ...', 'The Lean proof, on the other hand, was mostly translated from our natural language proof using LLMs, specifically GPT 5.4 through Codex and Claude Opus 4.6 through Claude Code, using the lean-lsp-mcp and custom skills.']
- PDF: https://arxiv.org/pdf/2607.06693.pdf

---
