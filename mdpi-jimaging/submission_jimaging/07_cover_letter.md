Sophie Zhu
Mira Costa High School, Manhattan Beach, CA 90266, USA
sophiezhu2028@gmail.com · ORCID 0009-0004-2403-910X

27 September 2026

Editorial Office, *Journal of Imaging*
MDPI

Dear Editor,

Please consider the enclosed manuscript, "When File Format Predicts the Label: A Case Study of Provenance Confounding in Medicine-Authenticity Image Classification", for publication as an Article in the *Journal of Imaging* Special Issue "Progress, Challenges, and Future Trends in Computer Vision and Pattern Recognition".

The paper is a case study of an evaluation failure in image classification. When the two classes of a dataset are collected by different routes, the collection route can predict the label, and because the association runs through the whole dataset, every train/test partition inherits it, including near-duplicate-grouped partitions. In a public counterfeit-medicine image dataset, file format alone reproduces all 510 source labels. Four model families, from a color-histogram baseline to a frozen EfficientNet-B0, reach internal accuracies of 0.838 to 0.974. On 150 independently acquired authentic photographs, three of them classify at most 9 correctly, and on a balanced external set of regulator-confirmed falsified products and authentic-labeled reference photographs, balanced accuracy is 0.391 to 0.609. Exploratory normalization of the measured acquisition statistics improves transfer under one capture condition but leaves the models dependent on the outer region of the frame.

We do not propose a new algorithm. The contribution is the integrated evaluation sequence, from a file-level provenance audit through leakage-controlled internal testing to two kinds of external evaluation, and what it shows on this dataset. The work fits the Special Issue's interest in robust and trustworthy visual recognition under changing acquisition conditions. Follow-up and exploratory analyses are identified as such. All code, split assignments, per-image statistics and predictions are public.

Generative AI (Claude, Anthropic) was used to draft and revise text, to write code, and to make a first pass at the per-image eligibility screens of the balanced external set's candidate images, every decision of which the author reviewed. This use is described in Section 2.5 and the Acknowledgments. The author reviewed all output and takes full responsibility for the content.

We confirm that neither the manuscript nor any part of its content is currently under consideration for publication with or published in another journal.

All authors have approved the manuscript and agree with its submission to the *Journal of Imaging*.

Sincerely,

Sophie Zhu
