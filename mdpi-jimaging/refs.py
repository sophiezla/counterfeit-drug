"""Reference database for the Journal of Imaging manuscript, and the converter.

manuscript_src.md cites by key ([@key] or [@a; @b]); this script numbers the
keys by first appearance, writes manuscript.md with MDPI [n] citations and the
reference list, and prints the Diagnostics-number -> J Imaging-number map used
to remap the supplement's citations.

Every entry below is copied from mdpi-diagnostics/manuscript.md (verified
there) except zhou and trivedi, which come from the IEEE record paper/paper.md
([23] and [10]), where they were verified against the publisher of record.

Usage: python refs.py
"""
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))

REFS = {
    "who": (1, "World Health Organization. Substandard and Falsified Medical Products. Available online: https://www.who.int/news-room/fact-sheets/detail/substandard-and-falsified-medical-products (accessed on 13 September 2026)."),
    "ozawa": (2, "Ozawa, S.; Evans, D.R.; Bessias, S.; Haynie, D.G.; Yemeke, T.T.; Laing, S.K.; Herrington, J.E. Prevalence and Estimated Economic Burden of Substandard and Falsified Medicines in Low- and Middle-Income Countries: A Systematic Review and Meta-analysis. *JAMA Netw. Open* **2018**, *1*, e181662. https://doi.org/10.1001/jamanetworkopen.2018.1662"),
    "ramos": (3, "Ramos, R.R.T.; Samonte, K.R.B.; Manlises, C.O. Medicine Authentication Based on Image Processing Using Convolutional Neural Networks. In Proceedings of the 16th International Conference on Computer and Automation Engineering (ICCAE), 2024; pp. 278–282. https://doi.org/10.1109/ICCAE59995.2024.10569752"),
    "motwani": (4, "Motwani, K.; Dsouza, R.; Dsouza, R.; Jose, J. Counterfeit Medicine Detection Using Deep Learning. *Int. J. Innov. Res. Technol.* **2022**, *9*, 818–821."),
    "thomsonyolo": (5, "Thomson, B.S.; Varuna, W.R. An Intelligent Counterfeit Medicine Classification Prediction System Using Modified YOLO: A Single Stage Object Detector. *TPM Test. Psychom. Methodol. Appl. Psychol.* **2025**, *32*, 1073–1088."),
    "thomsonijcrt": (6, "Thomson, B.S.; Varuna, W.R. Detecting Counterfeit Medicines Utilizing Artificial Intelligence Technique. *Int. J. Creat. Res. Thoughts* **2025**, *13*, i322–i329."),
    "ting": (7, "Ting, H.-W.; Chung, S.-L.; Chen, C.-F.; Chiu, H.-Y.; Hsieh, Y.-W. A Drug Identification Model Developed Using Deep Learning Technologies: Experience of a Medical Center in Taiwan. *BMC Health Serv. Res.* **2020**, *20*, 312. https://doi.org/10.1186/s12913-020-05166-w"),
    "alhussaeni": (8, "Al-Hussaeni, K.; Karamitsos, I.; Adewumi, E.; Amawi, R.M. CNN-Based Pill Image Recognition for Retrieval Systems. *Appl. Sci.* **2023**, *13*, 5050. https://doi.org/10.3390/app13085050"),
    "geirhos": (9, "Geirhos, R.; Jacobsen, J.-H.; Michaelis, C.; Zemel, R.; Brendel, W.; Bethge, M.; Wichmann, F.A. Shortcut Learning in Deep Neural Networks. *Nat. Mach. Intell.* **2020**, *2*, 665–673. arXiv:2004.07780."),
    "zech": (10, "Zech, J.R.; Badgeley, M.A.; Liu, M.; Costa, A.B.; Titano, J.J.; Oermann, E.K. Variable Generalization Performance of a Deep Learning Model to Detect Pneumonia in Chest Radiographs: A Cross-Sectional Study. *PLoS Med.* **2018**, *15*, e1002683. https://doi.org/10.1371/journal.pmed.1002683"),
    "hill": (11, "Hill, B.G.; Koback, F.L.; Schilling, P.L. The Risk of Shortcutting in Deep Learning Algorithms for Medical Imaging Research. *Sci. Rep.* **2024**, *14*, 29224. https://doi.org/10.1038/s41598-024-79838-6"),
    "seah": (12, "Seah, J.; Tang, C.; Buchlak, Q.D.; Milne, M.R.; Holt, X.; Ahmad, H.; Lambert, J.; Esmaili, N.; Oakden-Rayner, L.; Brotchie, P.; Jones, C.M. Do Comprehensive Deep Learning Algorithms Suffer from Hidden Stratification? A Retrospective Study on Pneumothorax Detection in Chest Radiography. *BMJ Open* **2021**, *11*, e053024. https://doi.org/10.1136/bmjopen-2021-053024"),
    "degrave": (13, "DeGrave, A.J.; Janizek, J.D.; Lee, S.-I. AI for Radiographic COVID-19 Detection Selects Shortcuts over Signal. *Nat. Mach. Intell.* **2021**, *3*, 610–619. https://doi.org/10.1038/s42256-021-00338-7"),
    "grommelt": (14, "Grommelt, P.; Weiss, L.; Pfreundt, F.-J.; Keuper, J. Fake or JPEG? Revealing Common Biases in Generated Image Detection Datasets. In *Computer Vision – ECCV 2024 Workshops*; Lecture Notes in Computer Science; Springer: Cham, Switzerland, 2025; pp. 80–95. https://doi.org/10.1007/978-3-031-92089-9_6"),
    "onglyp": (15, "Ong Ly, C.; Unnikrishnan, B.; Tadic, T.; Patel, T.; Duhamel, J.; Kandel, S.; Moayedi, Y.; Brudno, M.; Hope, A.; Ross, H.; McIntosh, C. Shortcut Learning in Medical AI Hinders Generalization: Method for Estimating AI Model Generalization without External Data. *npj Digit. Med.* **2024**, *7*, 124. https://doi.org/10.1038/s41746-024-01118-4"),
    "torralba": (16, "Torralba, A.; Efros, A.A. Unbiased Look at Dataset Bias. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 2011; pp. 1521–1528. https://doi.org/10.1109/CVPR.2011.5995347"),
    "drenkow": (17, "Drenkow, N.; Pavlak, M.; Harrigian, K.; Zirikly, A.; Subbaswamy, A.; Farhangi, M.M.; Petrick, N.; Unberath, M. Detecting Dataset Bias in Medical AI: A Generalized and Modality-Agnostic Auditing Framework. *arXiv* **2025**, arXiv:2503.09969."),
    "kaggle": (18, "Jha, S.K. Fake vs Real Medicine Dataset (Images). Kaggle. Available online: https://www.kaggle.com/datasets/surajkumarjha1/fake-vs-real-medicine-datasets-images (accessed on 13 September 2026)."),
    "oner": (19, "Öner, M.Ü.; Cheng, Y.-C.; Lee, H.K.; Sung, W.-K. Training Machine Learning Models on Patient Level Data Segregation Is Crucial in Practical Clinical Applications. *medRxiv* **2020**, preprint. https://doi.org/10.1101/2020.04.23.20076406"),
    "roboflow": (20, "Harshini, T.G.R. Counterfeit_med_detection, Version 4 (Multiclass Export). Roboflow Universe, November 2022. Available online: https://universe.roboflow.com/harshini-t-g-r/counterfeit_med_detection (accessed on 28 August 2026)."),
    "mendeley": (21, "Abdelmaksoud, E.; Gadallah, A.; Asad, A. Mobile-Captured Pharmaceutical Medication Packages. Mendeley Data, V1, 2022. https://doi.org/10.17632/bjy2svvmn8.1"),
    "zauner": (22, "Zauner, C. Implementation and Benchmarking of Perceptual Image Hash Functions. M.Sc. Thesis, Upper Austria University of Applied Sciences, Hagenberg, Austria, July 2010."),
    "mobilenet": (23, "Howard, A.; Sandler, M.; Chu, G.; Chen, L.-C.; Chen, B.; Tan, M.; Wang, W.; Zhu, Y.; Pang, R.; Vasudevan, V.; Le, Q.V.; Adam, H. Searching for MobileNetV3. In Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV), 2019; pp. 1314–1324. arXiv:1905.02244."),
    "efficientnet": (24, "Tan, M.; Le, Q.V. EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks. In Proceedings of the International Conference on Machine Learning (ICML), 2019. arXiv:1905.11946."),
    "hendrycks": (25, "Hendrycks, D.; Dietterich, T. Benchmarking Neural Network Robustness to Common Corruptions and Perturbations. In Proceedings of the International Conference on Learning Representations (ICLR), 2019. arXiv:1903.12261."),
    "gradcam": (26, "Selvaraju, R.R.; Cogswell, M.; Das, A.; Vedantam, R.; Parikh, D.; Batra, D. Grad-CAM: Visual Explanations from Deep Networks via Gradient-Based Localization. In Proceedings of the IEEE International Conference on Computer Vision (ICCV), 2017. arXiv:1610.02391."),
    "efron": (27, "Efron, B.; Tibshirani, R.J. *An Introduction to the Bootstrap*; Chapman & Hall: New York, NY, USA, 1993."),
    "mcnemar": (28, "McNemar, Q. Note on the Sampling Error of the Difference Between Correlated Proportions or Percentages. *Psychometrika* **1947**, *12*, 153–157."),
    "pytorch": (29, "Paszke, A.; Gross, S.; Massa, F.; et al. PyTorch: An Imperative Style, High-Performance Deep Learning Library. In Advances in Neural Information Processing Systems (NeurIPS), 2019."),
    "sklearn": (30, "Pedregosa, F.; Varoquaux, G.; Gramfort, A.; et al. Scikit-learn: Machine Learning in Python. *J. Mach. Learn. Res.* **2011**, *12*, 2825–2830."),
    "zhou": (None, "Zhou, K.; Liu, Z.; Qiao, Y.; Xiang, T.; Loy, C.C. Domain Generalization: A Survey. *IEEE Trans. Pattern Anal. Mach. Intell.* **2023**, *45*, 4396–4415. https://doi.org/10.1109/TPAMI.2022.3195549"),
    "trivedi": (None, "Trivedi, A.; Robinson, C.; Blazes, M.; Ortiz, A.; Desbiens, J.; Gupta, S.; Dodhia, R.; Bhatraju, P.K.; Liles, W.C.; Kalpathy-Cramer, J.; Lee, A.Y.; Lavista Ferres, J.M. Deep Learning Models for COVID-19 Chest X-ray Classification: Preventing Shortcut Learning Using Feature Disentanglement. *PLoS ONE* **2022**, *17*, e0274098. https://doi.org/10.1371/journal.pone.0274098"),
}

CITE = re.compile(r"\[(@[a-z0-9]+(?:;\s*@[a-z0-9]+)*)\]")


def compress(nums):
    nums = sorted(set(nums)); out = []; i = 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append(str(nums[i]) if j == i else (f"{nums[i]},{nums[j]}" if j == i + 1 else f"{nums[i]}–{nums[j]}"))
        i = j + 1
    return ",".join(out)


def main():
    src = io.open(os.path.join(HERE, "manuscript_src.md"), encoding="utf-8").read()
    order = []
    for m in CITE.finditer(src):
        for k in re.findall(r"@([a-z0-9]+)", m.group(1)):
            if k not in REFS:
                sys.exit(f"unknown key {k}")
            if k not in order:
                order.append(k)
    num = {k: i + 1 for i, k in enumerate(order)}
    unused = [k for k in REFS if k not in num]
    out = CITE.sub(lambda m: "[" + compress(num[k] for k in re.findall(r"@([a-z0-9]+)", m.group(1))) + "]", src)
    out = out.rstrip() + "\n\n" + "\n".join(f"{num[k]}. {REFS[k][1]}" for k in order) + "\n"
    io.open(os.path.join(HERE, "manuscript.md"), "w", encoding="utf-8", newline="\n").write(out)
    dmap = {REFS[k][0]: num[k] for k in order if REFS[k][0]}
    io.open(os.path.join(HERE, "_refmap_diag_to_jimaging.txt"), "w", encoding="utf-8").write(
        "\n".join(f"{a} -> {dmap.get(a, 'DROPPED')}" for a in range(1, 31)) + "\n")
    print(f"{len(order)} references cited; unused keys: {unused}")
    return dmap


if __name__ == "__main__":
    main()
