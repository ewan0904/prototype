# 🌱 Towards Sustainable Food Recommendations  
**Integrating Nutritional and Environmental Metrics**

[![Python](https://img.shields.io/badge/python-3.10.13-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-Streamlit-ff4b4b.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Last Updated](https://img.shields.io/badge/last%20updated-2025--09-lightgrey.svg)](#)

---

This prototype is a **Streamlit web application** connected with the [Langflow](https://www.langflow.org/) API (via [DataStax AstraDB](https://www.datastax.com/astra/db)) to make recipe recommendations for users.  
It contains ~5600 recipes and integrates **nutritional and environmental metrics** to support sustainable food choices.

This project was designed as part of my **Master Thesis at the [University of Twente](https://www.utwente.nl/)** in **Business Information Technology**.

A user study was conducted to evaluate the system, and it received **positive feedback**, with several improvement suggestions noted.  
For more details, please refer to the **full thesis** included in this repository.

📧 For further inquiries: [eric.wan0409@gmail.com](mailto:eric.wan0409@gmail.com)

---

## ✨ Key Features

- 🍲 Recipe retrieval with semantic search (Langflow + AstraDB)
- ⚖️ Health/Environment scoring model
- ⚙️ Adjustable weighting between all metrics
- 📊 Transparent score breakdown (nutrition, environment, and calculation views)

---

## 🧩 High-Level Architecture

<!-- Replace the path below with the actual image path in your repo -->
![High-Level Architecture](images/architecture.png)

---

## 📚 Data Sources

- [Agribalyse](https://agribalyse.ademe.fr/) — Environmental metrics  
- [NEVO](https://nevo-online.rivm.nl/) — Nutritional metrics  
- [BBC Good Food](https://www.bbcgoodfood.com/) — Recipe dataset  

---

## ⚙️ Installation

1. Use **Python 3.10.13** (recommended — other versions not tested)
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
