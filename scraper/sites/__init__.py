from scraper.sites.jobkorea import scrape_jobkorea
from scraper.sites.saramin import scrape_saramin
from scraper.sites.wanted import scrape_wanted
from scraper.sites.jumpit import scrape_jumpit
from scraper.sites.rocketpunch import scrape_rocketpunch

ALL_SCRAPERS = [
    scrape_jobkorea,
    scrape_saramin,
    scrape_wanted,
    scrape_jumpit,
    scrape_rocketpunch,
]
