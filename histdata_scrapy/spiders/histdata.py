# -*- coding: utf-8 -*-
import scrapy
from zipfile import ZipFile
from io import BytesIO
import pandas as pd


class HistDataSpider(scrapy.Spider):
    name = 'histdata'
    allowed_domains = ['histdata.com']
    start_urls = ['http://www.histdata.com/download-free-forex-data/?/ascii/tick-data-quotes']

    target_fxpairs = ["USD/JPY", "EUR/USD"]
    # target_month = (2019, 8)
    target_month = None

    def parse(self, response):
        self.logger.info(f"parse: url={response.url}")

        for link_cell in response.xpath("//div[@id='content']/div/table/tr/td"):
            url = link_cell.xpath("a/@href").extract()[0]
            url = response.urljoin(url)
            fxpair = link_cell.xpath("a/strong/text()").extract()[0]

            self.logger.info(f"fxpair={fxpair}, url={url}")

            if fxpair not in self.target_fxpairs:
                continue

            yield scrapy.Request(url, callback=self.parse_years)

    def parse_years(self, response):
        self.logger.info(f"parse_years: url={response.url}")

        for link_cell in response.xpath("//div[@class='page-content']/table/tr/td"):
            url = link_cell.xpath("a/@href").extract()[0]
            url = response.urljoin(url)
            year = int(link_cell.xpath("a/strong/text()").extract()[0])

            self.logger.info(f"year={year}, url={url}")

            if self.target_month is not None:
                if self.target_month[0] != year:
                    continue

            yield scrapy.Request(url, callback=self.parse_months)

    def parse_months(self, response):
        self.logger.info(f"parse_months: url={response.url}")

        for link in response.xpath("//div[@class='page-content']/p/a"):
            url = link.xpath("@href").extract()[0]
            url = response.urljoin(url)
            year = int(url.split("/")[-2])
            month = int(url.split("/")[-1])

            self.logger.info(f"year={year}, month={month}, url={url}")

            if self.target_month is not None:
                if self.target_month[0] != year or self.target_month[1] != month:
                    continue

            yield scrapy.Request(url, callback=self.parse_download)

    def parse_download(self, response):
        self.logger.info(f"parse_download: url={response.url}")

        for form_node in response.xpath("//form[@id='file_down']"):
            url = form_node.xpath("@action").extract()[0]
            url = response.urljoin(url)

            params = {
                "tk": form_node.xpath("input[@id='tk']/@value").extract()[0],
                "date": form_node.xpath("input[@id='date']/@value").extract()[0],
                "datemonth": form_node.xpath("input[@id='datemonth']/@value").extract()[0],
                "platform": form_node.xpath("input[@id='platform']/@value").extract()[0],
                "timeframe": form_node.xpath("input[@id='timeframe']/@value").extract()[0],
                "fxpair": form_node.xpath("input[@id='fxpair']/@value").extract()[0]
            }

            self.logger.info(f"url={url}, params={params}")

            yield scrapy.FormRequest(url, formdata=params, callback=self.parse_zip_download)

    def parse_zip_download(self, response):
        self.logger.info(f"parse_zip_download: content-type={response.headers['Content-Type']}, size={len(response.body)}")

        with BytesIO(response.body) as buf:
            with ZipFile(buf) as dl_zip:
                for file_name in dl_zip.namelist():
                    if file_name.endswith(".csv"):
                        with BytesIO(dl_zip.read(file_name)) as csv_buf:
                            df = pd.read_csv(csv_buf, names=["datetime", "bid", "ask", "volume"])
                            self.logger.info(df)
