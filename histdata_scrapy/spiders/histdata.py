# -*- coding: utf-8 -*-
import scrapy


class HistDataSpider(scrapy.Spider):
    name = 'histdata'
    allowed_domains = ['histdata.com']
    start_urls = ['http://www.histdata.com/download-free-forex-data/?/ascii/tick-data-quotes']

    def parse(self, response):
        print("*** parse ***")

        for link_cell in response.xpath("//div[@id='content']/div/table/tr/td"):
            print(link_cell.xpath("a/@href").extract()[0])
