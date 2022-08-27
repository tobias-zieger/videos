from scrapers.kikascraper import KikaScraper
from scrapers.metascrapers.logoscraper import LogoScraper
from scrapers.metascrapers.sachgeschichtenmetascraper import \
    SachgeschichtenMetaScraper
from scrapers.metascrapers.wildeweltmetascraper import WildeWeltMetaScraper

SOURCES = {
    KikaScraper(
        name='Wir Kinder aus dem Möwenweg',
        link='https://www.kika.de/wir-kinder-aus-dem-moewenweg/buendelgruppe2252.html',
    ),
    LogoScraper(),
    SachgeschichtenMetaScraper(),
    WildeWeltMetaScraper(),
}
