Sophie Zhu
Mira Costa High School, Manhattan Beach, CA 90266, USA
sophiezhu2028@gmail.com · ORCID 0009-0004-2403-910X

23 September 2026

Editorial Office, *Diagnostics*
MDPI

Dear Editor,

Please consider the enclosed manuscript, "Auditing Provenance Confounding in Image Authenticity Classification: A Counterfeit-Medicine Case Study", for publication as an Article in *Diagnostics*.

Image-based screening of medicine packaging is increasingly proposed as a triage tool against substandard and falsified medical products, and published classifiers report high accuracy. In the studies we located, each group built its own image set, and in some the counterfeit images were produced by a different route from the authentic ones. When that happens, the acquisition route alone can predict the label, and any validation drawn from the same pool will not reveal it.

The manuscript describes a simple provenance audit that tests for this before any model is trained, by fitting the intended classifier to acquisition metadata alone. We apply it to a public counterfeit-medicine dataset. Container format alone predicts all 510 labels. Four model families nevertheless reach internal accuracy of 0.838 to 0.987, and a near-duplicate-grouped split changes that by at most 6.8 points. On independently acquired photographs the model with the highest internal accuracy correctly classifies 9 of 150 authentic images. On a balanced external set of regulator-confirmed falsified products, three of the four models perform at chance. An exploratory analysis shows that removing the audited acquisition statistics leaves the corrected models dependent on the outer region of the frame, so the audit should be repeated after any correction.

We believe the work fits the scope of *Diagnostics* because it concerns the validity of evaluation for image-based screening systems, in particular dataset quality assurance and external validation, which apply broadly to diagnostic imaging AI. The audit needs no new data or model training. All code, split assignments and per-image statistics are public, and every table can be regenerated from committed artifacts.

Generative AI (Claude, Anthropic) was used to assist in drafting and revising text, in writing code, and in one data-producing task: a per-image subject-matter eligibility screen of candidate photographs. This use is described in Section 2.12 and the Acknowledgments. The author reviewed all output and takes full responsibility for the content.

We confirm that neither the manuscript nor any parts of its content are currently under consideration for publication with or published in another journal.

All authors have approved the manuscript and agree with its submission to *Diagnostics*.

Sincerely,

Sophie Zhu
