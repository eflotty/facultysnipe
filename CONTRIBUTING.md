# Contributing to FacultySnipe

Thank you for your interest in contributing to FacultySnipe! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/yourusername/FacultySnipe/issues)
2. If not, create a new issue with:
   - Clear title describing the bug
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Environment details (OS, Python version, etc.)
   - Relevant logs or screenshots

### Suggesting Enhancements

1. Check if the enhancement has been suggested
2. Create a new issue with:
   - Clear title describing the enhancement
   - Detailed description of the proposed feature
   - Use cases and benefits
   - Potential implementation approach (optional)

### Adding New University Scrapers

This is the most common contribution!

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/FacultySnipe.git
   cd FacultySnipe
   git checkout -b feature/add-stanford-biology
   ```

2. **Create the scraper**
   ```bash
   cp src/universities/template.py src/universities/stanford_biology.py
   ```

3. **Implement the parser**
   - Analyze the target page structure
   - Choose StaticScraper or DynamicScraper
   - Implement the `parse()` method
   - Add proper error handling

4. **Test locally**
   ```bash
   cd src
   python main.py --university stanford_biology
   ```

5. **Add test data**
   - Update CONFIG sheet example in README if needed
   - Add example output in PR description

6. **Submit Pull Request**
   - Clear title: "Add scraper for Stanford Biology"
   - Description with:
     - University name and department
     - URL to faculty page
     - Scraper type (static/dynamic)
     - Test results
     - Any special considerations

### Code Style Guidelines

#### Python Code Style

- Follow PEP 8
- Use type hints where appropriate
- Maximum line length: 100 characters
- Use docstrings for all classes and methods

Example:
```python
def parse(self, soup: BeautifulSoup) -> List[Faculty]:
    """
    Parse faculty data from HTML

    Args:
        soup: BeautifulSoup parsed HTML

    Returns:
        List of Faculty objects
    """
    # Implementation
```

#### Naming Conventions

- **Scraper files**: `university_department.py` (lowercase, underscores)
- **Scraper classes**: `UniversityDepartmentScraper` (PascalCase)
- **University IDs**: `university_dept` (lowercase, underscores)
- **Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`

#### Scraper Best Practices

1. **Use helper methods**
   ```python
   email = self._extract_email(card)  # Don't reimplement
   text = self._clean_text(raw_text)  # Use provided helpers
   ```

2. **Handle missing data gracefully**
   ```python
   title = None
   title_elem = card.select_one('.title')
   if title_elem:
       title = self._clean_text(title_elem.get_text())
   ```

3. **Try multiple selectors**
   ```python
   name = None
   for selector in ['.name', '.person-name', 'h2', 'h3']:
       name_elem = card.select_one(selector)
       if name_elem:
           name = self._clean_text(name_elem.get_text())
           break
   ```

4. **Log useful information**
   ```python
   self.logger.info(f"Found {len(faculty_cards)} faculty cards")
   self.logger.warning(f"Failed to parse card: {e}")
   ```

5. **Make URLs absolute**
   ```python
   if profile_url.startswith('/'):
       profile_url = f"https://university.edu{profile_url}"
   ```

### Testing

#### Unit Tests

Add tests for new functionality:

```python
# tests/test_your_scraper.py
import unittest
from universities.your_scraper import YourScraper

class TestYourScraper(unittest.TestCase):
    def test_scraping(self):
        # Test implementation
        pass
```

Run tests:
```bash
python -m pytest tests/ -v
```

#### Integration Testing

Test your scraper end-to-end:
```bash
cd src
python main.py --university your_university_id
```

Verify:
- [ ] Faculty data appears in Google Sheets
- [ ] All expected fields are populated
- [ ] No errors in logs
- [ ] Email notification sent (if changes detected)

### Pull Request Process

1. **Update documentation**
   - Update README.md if adding new features
   - Add university to list of supported institutions
   - Update SETUP_GUIDE.md if changing setup process

2. **Check your changes**
   ```bash
   # Run tests
   python -m pytest tests/

   # Check code style
   flake8 src/ --max-line-length=100

   # Test locally
   python src/main.py --university your_university
   ```

3. **Create Pull Request**
   - Use clear, descriptive title
   - Reference related issues (#123)
   - Describe what changed and why
   - Include test results
   - Add screenshots if relevant

4. **Code Review**
   - Address reviewer feedback
   - Make requested changes
   - Keep discussion focused and professional

5. **Merge**
   - Maintainers will merge once approved
   - Delete your feature branch after merge

### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/FacultySnipe.git
cd FacultySnipe

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Install development dependencies
pip install pytest flake8 black mypy

# Configure pre-commit hook (optional)
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
python -m pytest tests/
flake8 src/ --max-line-length=100
EOF
chmod +x .git/hooks/pre-commit
```

### Commit Message Guidelines

Use clear, descriptive commit messages:

**Good:**
```
Add scraper for Stanford Biology department
Fix email extraction for Miami scraper
Update README with new setup instructions
```

**Bad:**
```
Fixed stuff
Update
WIP
```

Use conventional commits (optional but encouraged):
```
feat: Add scraper for Stanford Biology
fix: Correct email extraction in Miami scraper
docs: Update README with setup instructions
test: Add unit tests for base scraper
refactor: Simplify faculty ID generation
```

### Issue Labels

- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Documentation improvements
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `university scraper` - New university scraper
- `question` - Further information requested

### Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Welcome newcomers
- Help others learn

### Questions?

- Open an issue with the `question` label
- Check existing issues and documentation first
- Be specific about what you need help with

### Recognition

Contributors will be recognized in:
- README.md Contributors section
- Release notes for their contributions
- Project documentation

Thank you for contributing to FacultySnipe!
