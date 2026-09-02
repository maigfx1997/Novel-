import * as cheerio from "cheerio";

export interface NovlarChapter {
  id: string;
  title: string;
  url: string;
  chapterNum: number;
  content?: string;
  images?: string[];
}

export interface NovlarNovel {
  id: string;
  title: string;
  author: string;
  description: string;
  cover: string;
  chapters: NovlarChapter[];
}

const BASE_URL = "https://www.novlar.com";

const HEADERS = {
  "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  Accept:
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
  "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
  "Accept-Encoding": "gzip, deflate, br",
  Connection: "keep-alive",
};

export async function fetchNovlarNovel(url: string): Promise<NovlarNovel> {
  // Extract novel ID from URL
  const idMatch = url.match(/[?&]id=(\d+)/) || url.match(/\/novel\/(\d+)/);
  if (!idMatch) {
    throw new Error("Invalid Novlar novel URL");
  }
  const novelId = idMatch[1];

  const novelUrl = `${BASE_URL}/views/novel/details.php?id=${novelId}`;

  const response = await fetch(novelUrl, { headers: HEADERS });
  if (!response.ok) {
    throw new Error(`Failed to fetch Novlar novel: ${response.status}`);
  }

  const html = await response.text();
  const $ = cheerio.load(html);

  // Extract title from h1 or title tag
  const title =
    $("h1.novel-title, .novel-info h1").first().text().trim() ||
    $("h1").first().text().trim() ||
    $("title").text().replace("- نوفلار", "").trim();

  // Extract author - look for author links
  const author =
    $("a[href*='author-profile']").first().text().trim() ||
    $(".author-name, .author-meta span").first().text().trim() ||
    "Unknown";

  // Extract description
  const description =
    $("#synopsisText").text().trim() ||
    $(".synopsis, .description, .summary").text().trim();

  // Extract cover
  const cover =
    $(".cover-img").attr("src") ||
    $(".cover-wrapper img").attr("src") ||
    $("img[alt='غلاف']").attr("src") ||
    "";

  // Extract chapters from the chapters tab
  const chapters: NovlarChapter[] = [];

  // Find chapter items in the chapters list
  $("a.chapter-item, #tab-chapters a.chapter-item, .chapters-list a").each(
    (i, el) => {
      const href = $(el).attr("href") || "";
      const postIdMatch = href.match(/post_id=(\d+)/);

      if (postIdMatch) {
        const chapterTitle =
          $(el).find("strong").text().trim() ||
          $(el).find(".chapter-title").text().trim() ||
          $(el).text().trim().split("\n")[0];

        const chapterNumText = $(el).find("small").text().trim();
        const chapterNum =
          parseInt(chapterNumText.replace(/[^\d]/g, "")) || i + 1;

        chapters.push({
          id: postIdMatch[1],
          title: chapterTitle || `الفصل ${chapterNum}`,
          url: href.startsWith("http")
            ? href
            : href.startsWith("/")
              ? `${BASE_URL}${href}`
              : `${BASE_URL}/views/novel/${href}`,
          chapterNum,
        });
      }
    }
  );

  // Sort by chapter number
  chapters.sort((a, b) => a.chapterNum - b.chapterNum);

  return {
    id: novelId,
    title,
    author,
    description,
    cover,
    chapters,
  };
}

export async function fetchNovlarChapterContent(
  chapterUrl: string
): Promise<{ content: string; images: string[] }> {
  const fullUrl = chapterUrl.startsWith("http")
    ? chapterUrl
    : chapterUrl.startsWith("/")
      ? `${BASE_URL}${chapterUrl}`
      : `${BASE_URL}/views/novel/${chapterUrl}`;

  const response = await fetch(fullUrl, { headers: HEADERS });
  if (!response.ok) {
    throw new Error(`Failed to fetch Novlar chapter: ${response.status}`);
  }

  const html = await response.text();
  const $ = cheerio.load(html);

  // Extract images
  const images: string[] = [];
  const paragraphsHtml: string[] = [];

  // Look for paragraph wrappers with content
  $(".paragraph-wrapper, #chapterContent .paragraph-wrapper").each((_, el) => {
    // Get any images in the paragraph
    $(el).find("img").each((__, img) => {
      const src = $(img).attr("src");
      if (src) {
        images.push(src);
      }
    });

    // Get the paragraph content div
    const contentDiv = $(el).find(".paragraph-content");
    const paraHtml = contentDiv.html() || contentDiv.text();

    if (paraHtml && paraHtml.trim()) {
      // Extract text and images
      const imgTags = $(el).find("img").map((__, img) => {
        const src = $(img).attr("src");
        return src ? `<img src="${src}" style="max-width:100%;border-radius:8px;margin:10px 0" alt=""/>` : "";
      }).get().join("");

      const text = contentDiv.text().trim();
      if (text) {
        paragraphsHtml.push(
          `<p style="direction:rtl;text-align:right;line-height:2;margin-bottom:16px;font-size:18px">${text}${imgTags}</p>`
        );
      } else if (imgTags) {
        paragraphsHtml.push(`<div style="text-align:center;margin:16px 0">${imgTags}</div>`);
      }
    }
  });

  // Fallback: look for chapter-content div
  if (paragraphsHtml.length === 0) {
    const contentEl = $("#chapterContent, .chapter-content");
    contentEl.find("img").each((_, img) => {
      const src = $(img).attr("src");
      if (src) images.push(src);
    });

    contentEl.find("p").each((_, el) => {
      const text = $(el).text().trim();
      if (text) {
        paragraphsHtml.push(
          `<p style="direction:rtl;text-align:right;line-height:2;margin-bottom:16px;font-size:18px">${text}</p>`
        );
      }
    });
  }

  const content = `<div dir="rtl" style="text-align:right;font-family:'Tajawal',serif">${paragraphsHtml.join("\n")}</div>`;

  return { content, images };
}
