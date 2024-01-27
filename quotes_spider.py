import scrapy

class ProductScraper(scrapy.Spider):
    name = "product_scraper"

    # Replace with the URL of the page listing categories
    start_urls = ['https://almeera.online/']

    # Set the maximum number of categories, subcategories, and products to extract
    max_categories = 5  # Example: Limit to 5 categories
    max_subcategories = 5  # Example: Limit to 10 subcategories per category
    max_products = 5  # Example: Limit to 20 products per subcategory

    scrapped_data = []

    def parse(self, response):
        # Extract category URLs and category image URLs
        category_links = response.css(
            '#content > div > div > div.block.block-block.block-subcategories > div > ul > li > a::attr(href)').getall()
        category_image_urls = response.css(
            '.subcategory-icon img::attr(src)').getall()

        # Loop through category links and image URLs
        download_images = []
        for index, (category_link, category_image_url) in enumerate(zip(category_links, category_image_urls)):
            download_images.append(response.urljoin(category_image_url))
            data = {
                "CategoryImageURL": response.urljoin(category_image_url),
                "Subcategories": [],
            }
            yield response.follow(category_link, self.parse_category, meta={"data": data})
            yield {
                "image_urls":download_images
            }
            if self.max_categories != -1 and index + 1 >= self.max_categories:
                break

    def parse_category(self, response):
        data = response.meta["data"]
        data["CategoryTitle"] = response.css('#page-title::text').get()

        yield data

        # Iterate over subcategories
        for index, subcategory_link in enumerate(response.css('#content .clearfix a::attr(href)').getall()):
            yield response.follow(subcategory_link, self.parse_subcategory, meta={'data': data["CategoryTitle"]})

            if self.max_subcategories != -1 and index + 1 >= self.max_subcategories:
                break

    def parse_subcategory(self, response):
        # Extract data for the current subcategory
        subcategory = {
            "catagoryIdentifier": response.meta['data'],
            "SubcategoryTitle": response.css('#page-title::text').get(),
            "Products": [],
        }

        yield subcategory

        # Iterate over product links within subcategories
        products_links = response.css(
            '.filtered-products .product-thumbnail::attr(href)').getall()
        
        download_images = []
        for index, product_link in enumerate(products_links):
            # Use `yield` to send the item to the `parse_subcategory` method
            myImage = response.urljoin(response.css('.photo.product-thumbnail::attr(src)').get())
            download_images.append(myImage)
            yield response.follow(product_link, self.parse_product, meta={'subcategory': subcategory})

            if self.max_products != -1 and index + 1 >= self.max_products:
                break
        yield {
            "image_urls":download_images
        }
        # Yield the subcategory with the populated Products list

    def parse_product(self, response):
        images_down = []
        myImage = response.urljoin( response.css('.photo.product-thumbnail::attr(src)').get())
        images_down.append(myImage)
        item = {
            'catagoryIdentifier': response.meta['subcategory']['catagoryIdentifier'],
            "subcategoryIdentifier": response.meta['subcategory']['SubcategoryTitle'],
            "ItemTitle": scrapy.Selector(text=response.css('.title').getall()[1]).css('::text').get(),
            "ItemImageURL":response.urljoin( response.css('.photo.product-thumbnail::attr(src)').get()),
            "ItemPrice": response.css('.product-details-info .price::text').get(),
            "ItemBarcode": response.css('.value::text').get(),
        }

        yield item
        yield {
            "image_urls":images_down
        }
