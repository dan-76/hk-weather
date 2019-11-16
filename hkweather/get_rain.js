const puppeteer = require('puppeteer');

[targetUrl, maxRetry] = process.argv.slice(2,4);

(async () => {
    const browser = await puppeteer.launch({headless: false, 
                                            executablePath: 'chromium-browser',
                                            args: ['--display=:0']});
    const page = await browser.newPage();
    await page.goto(targetUrl);
    await page.waitForSelector('#timeSeriesImg04');
    
    let trial = 0;
    do {
        var news = await page.evaluate(() => {
            var imgele = document.querySelectorAll('[id^=timeSeriesImg0]');
            var titleLinkArray = [];
            for (var i = 0; i < imgele.length; i++){
                titleLinkArray[i] = {
                    alt: imgele[i].getAttribute('alt'),
                    src: imgele[i].getAttribute('src')
                };
        
            }
            
            return titleLinkArray;
        });
        trial++;
        
        await page.reload();
        await page.waitForSelector('#timeSeriesImg04');

    } while ((trial < parseInt(maxRetry)) && (news.some(e => e.src == null)))
    
    await browser.close();
    const data = JSON.stringify(news);
    console.log(data);
})()

