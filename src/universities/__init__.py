"""
University scrapers package
"""
# Import all scraper classes here for easier access
# Add new scrapers as they are created

try:
    from .miami import MiamiMicrobiologyScraper
except ImportError:
    pass

try:
    from .uf_biochem import UFBiochemScraper
except ImportError:
    pass

# Add more imports as new universities are added
# from .stanford_biology import StanfordBiologyScraper
# from .harvard_chemistry import HarvardChemistryScraper
