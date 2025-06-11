# Prompt Engineering for Automated Essay Scoring

This project implements an automated essay scoring system using prompt engineering techniques, specifically designed for IELTS writing tasks. The system leverages state-of-the-art language models and prompt engineering to provide accurate and consistent essay scoring.

## Project Overview

The system uses prompt engineering to guide a pre-trained language model (DistilBERT) in scoring essays based on IELTS criteria. It processes essays through carefully crafted prompts that incorporate the scoring rubrics, enabling the model to generate scores between 0 and 9.

### Key Features

- Automated essay scoring using prompt engineering
- Support for IELTS writing task scoring criteria
- Preprocessing and cleaning of essay text
- Evaluation metrics including MSE and R² score
- Comprehensive documentation and research paper

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd essay-scoring
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Prepare your dataset in CSV format with 'Essay' and 'Overall' columns
2. Run the essay scorer:
```python
from essay_scorer import EssayScorer

# Initialize the scorer
scorer = EssayScorer()

# Score a single essay
score = scorer.score_essay("Your essay text here")

# Evaluate on a dataset
mse, r2 = scorer.evaluate(test_essays, test_scores)
```

## Project Structure

- `essay_scorer.py`: Main implementation of the essay scoring system
- `requirements.txt`: Project dependencies
- `research_paper.tex`: LaTeX template for the research paper
- `references.bib`: Bibliography for the research paper

## Scoring Criteria

The system evaluates essays based on IELTS writing criteria:
- Task Achievement
- Coherence and Cohesion
- Lexical Resource
- Grammatical Range and Accuracy

## Model Architecture

The system uses DistilBERT as the base model, enhanced with:
- Custom prompt templates
- Scoring criteria integration
- Post-processing for score normalization

## Evaluation

The system is evaluated using:
- Mean Squared Error (MSE)
- R² Score
- Cross-validation on the IELTS dataset

## Research Paper

A comprehensive research paper is included in LaTeX format, covering:
- Introduction and background
- Related work
- Methodology
- Experimental results
- Discussion and conclusions

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- The project uses the IELTS writing scored essays dataset
- Built with Hugging Face Transformers and PyTorch
- Inspired by recent advances in prompt engineering 