# -*- coding: utf-8 -*-
import scrapy

from ..app_logging import get_app_logger


class HistDataSpider(scrapy.Spider):
    name = 'histdata'
    allowed_domains = ['histdata.com']
    start_urls = ['http://www.histdata.com/download-free-forex-data/?/ascii/tick-data-quotes']

    target_fxpairs = ["USD/JPY", "EUR/USD"]
    # target_month = (2019, 8)
    target_month = None

    L = get_app_logger()

    def parse(self, response):
        self.L.info(f"parse: url={response.url}")

        for link_cell in response.xpath("//div[@id='content']/div/table/tr/td"):
            url = link_cell.xpath("a/@href").extract()[0]
            url = response.urljoin(url)
            fxpair = link_cell.xpath("a/strong/text()").extract()[0]

            self.L.info(f"fxpair={fxpair}, url={url}")

            if fxpair not in self.target_fxpairs:
                continue

            yield scrapy.Request(url, callback=self.parse_years)

    def parse_years(self, response):
        self.L.info(f"parse_years: url={response.url}")

        for link_cell in response.xpath("//div[@class='page-content']/table/tr/td"):
            url = link_cell.xpath("a/@href").extract()[0]
            url = response.urljoin(url)
            year = int(link_cell.xpath("a/strong/text()").extract()[0])

            self.L.info(f"year={year}, url={url}")

            if self.target_month is not None:
                if self.target_month[0] != year:
                    continue

            yield scrapy.Request(url, callback=self.parse_months)

    def parse_months(self, response):
        self.L.info(f"parse_months: url={response.url}")

        for link in response.xpath("//div[@class='page-content']/p/a"):
            url = link.xpath("@href").extract()[0]
            url = response.urljoin(url)
            year = int(url.split("/")[-2])
            month = int(url.split("/")[-1])

            self.L.info(f"year={year}, month={month}, url={url}")

            if self.target_month is not None:
                if self.target_month[0] != year or self.target_month[1] != month:
                    continue

            yield scrapy.Request(url, callback=self.parse_download)

    def parse_download(self, response):
        self.L.info(f"parse_download: url={response.url}")
