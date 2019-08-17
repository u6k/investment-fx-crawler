# -*- coding: utf-8 -*-
import scrapy
from zipfile import ZipFile
from io import BytesIO
import pandas as pd
from sqlalchemy import create_engine
import os


class HistDataSpider(scrapy.Spider):
    name = 'histdata'
    allowed_domains = ['histdata.com']
    start_urls = ['http://www.histdata.com/download-free-forex-data/?/ascii/tick-data-quotes']

    target_fxpairs = ["USD/JPY", "EUR/USD"]
    target_month = (2019, 8)
    # target_month = None

    def parse(self, response):
        self.logger.info(f"parse: url={response.url}")

        for link_cell in response.xpath("//div[@id='content']/div/table/tr/td"):
            url = link_cell.xpath("a/@href").extract()[0]
            url = response.urljoin(url)
            fxpair = link_cell.xpath("a/strong/text()").extract()[0]

            self.logger.info(f"fxpair={fxpair}, url={url}")

            if fxpair not in self.target_fxpairs:
                continue

            yield scrapy.Request(url, callback=self.parse_years, meta={"fxpair": fxpair})

    def parse_years(self, response):
        fxpair = response.meta["fxpair"]
        self.logger.info(f"parse_years: url={response.url}, fxpair={fxpair}")

        for link_cell in response.xpath("//div[@class='page-content']/table/tr/td"):
            url = link_cell.xpath("a/@href").extract()[0]
            url = response.urljoin(url)
            year = int(link_cell.xpath("a/strong/text()").extract()[0])

            self.logger.info(f"year={year}, url={url}")

            if self.target_month is not None:
                if self.target_month[0] != year:
                    continue

            yield scrapy.Request(url, callback=self.parse_months, meta={"fxpair": fxpair, "year": year})

    def parse_months(self, response):
        fxpair = response.meta["fxpair"]
        year = response.meta["year"]
        self.logger.info(f"parse_months: url={response.url}, fxpair={fxpair}, year={year}")

        for link in response.xpath("//div[@class='page-content']/p/a"):
            url = link.xpath("@href").extract()[0]
            url = response.urljoin(url)
            month = int(url.split("/")[-1])

            self.logger.info(f"month={month}, url={url}")

            if self.target_month is not None:
                if self.target_month[0] != year or self.target_month[1] != month:
                    continue

            yield scrapy.Request(url, callback=self.parse_download, meta={"fxpair": fxpair, "year": year, "month": month})

    def parse_download(self, response):
        fxpair = response.meta["fxpair"]
        year = response.meta["year"]
        month = response.meta["month"]
        self.logger.info(f"parse_download: url={response.url}, fxpair={fxpair}, year={year}, month={month}")

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

            yield scrapy.FormRequest(url, formdata=params, callback=self.parse_zip_download, meta={"fxpair": fxpair, "year": year, "month": month})

    def parse_zip_download(self, response):
        fxpair = response.meta["fxpair"]
        year = response.meta["year"]
        month = response.meta["month"]
        self.logger.info(f"parse_zip_download: content-type={response.headers['Content-Type']}, size={len(response.body)}, fxpair={fxpair}, year={year}, month={month}")

        with BytesIO(response.body) as buf:
            with ZipFile(buf) as dl_zip:
                for file_name in dl_zip.namelist():
                    if file_name.endswith(".csv"):
                        with BytesIO(dl_zip.read(file_name)) as csv_buf:
                            df = pd.read_csv(csv_buf, names=["timestamp_str", "bid", "ask", "volume"])
                            df["timestamp"] = pd.to_datetime(df["timestamp_str"] + "000", format="%Y%m%d %H%M%S%f") + pd.Timedelta(hours=5)
                            df = df.set_index("timestamp")

                            self.logger.info(df)

                            for freq in ["S", "10S", "T", "H", "D"]:
                                df_ohlc = df["ask"].resample(freq).ohlc().dropna()
                                df_ohlc["fxpair"] = fxpair
                                df_ohlc["freq"] = freq
                                df_ohlc["timestamp"] = df_ohlc.index
                                df_ohlc["id"] = df_ohlc["fxpair"].str[:3] + df_ohlc["fxpair"].str[-3:] + "_" + df_ohlc["freq"] + "_" + df_ohlc["timestamp"].dt.strftime("%Y%m%d%H%M%S%f")
                                df_ohlc = df_ohlc.set_index("id")

                                self.logger.info(df_ohlc)

                                self.logger.info(f"insert into db start. rows={len(df_ohlc)}")
                                df_ohlc.to_sql(name="historical", con=self.get_db_connection(), if_exists="append", index_label="id")
                                self.logger.info("insert into db finish.")

    def get_db_connection(self):
        url = f"postgresql://{os.environ['DB_USERNAME']}:{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_DATABASE']}"
        return create_engine(url)
