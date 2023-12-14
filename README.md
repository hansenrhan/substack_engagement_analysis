# substack_engagement_analysis

This repository contains tools for scraping and analyzing Substack blogs to understand reader engagement patterns. The project consists of the following components:

- `build_substack_database.ipynb`: A Jupyter notebook that identifies Substack blogs to scrape, downloads articles, calculates article metrics, and stores the data in a database.

- `substack_article_text_analysis.ipynb`: A Jupyter notebook that analyzes whether article metrics are associated with engagement, conducts topic modeling using Latent Dirichlet Allocation (LDA), and explores topics associated with reader engagement.

- `utils.py`: A Python script containing miscellaneous helper functions used in collecting, processing, and analyzing the data.


## Requirements

This project relies on various Python libraries for data collection, analysis, and visualization. You can install these dependencies using the following command:

```bash
pip install -r requirements.txt
```

## How To Use

1. Open `build_substack_database.ipynb` to collect Substack blog data and calculate article metrics.

2. Proceed to `substack_article_text_analysis.ipynb` to conduct further analysis, including NLP analysis and topic modeling.

3. Utilize functions from `utils.py` for additional tasks or custom analysis as needed.

