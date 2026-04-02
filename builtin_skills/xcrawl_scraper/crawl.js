import { createCrawl } from 'x-crawl'

const targetUrl = process.argv[2];
if (!targetUrl) {
  console.error("❌ 缺少URL参数！用法: node crawl.js <URL>");
  process.exit(1);
}

// 创建爬虫实例，深度伪装人类浏览器
const crawlApp = createCrawl({
  maxRetry: 3,
  intervalTime: { max: 3000, min: 1500 },
  userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
});

crawlApp.crawlHTML(targetUrl).then((res) => {
  if (res.isSuccess) {
    const { $ } = res.data;
    // 深度去噪：干掉所有干扰元素，只留正文干货
    $('script, style, nav, footer, header, aside, .ad, .advertisement, .comment, .sidebar').remove();
    // 针对网文平台优化：优先提取章节正文
    let text = '';
    const novelSelectors = ['.chapter-content', '.read-content', '#content', '.article-content', '.main-content'];
    for (const selector of novelSelectors) {
      if ($(selector).length > 0) {
        text = $(selector).text().replace(/\s+/g, ' ').trim();
        break;
      }
    }
    // 如果没找到网文正文，提取body文本
    if (!text) {
      text = $('body').text().replace(/\s+/g, ' ').trim();
    }
    // 截取前10000个字符，防止上下文溢出
    console.log(text.substring(0, 10000));
  } else {
    console.error(`❌ 抓取失败: ${targetUrl}`);
  }
});
