import * as cheerio from "cheerio";

export interface UranusChapter {
  id: number;
  title: string;
  url: string;
  chapterNum: number;
  content?: string;
  images?: string[];
}

export interface UranusNovel {
  id: string;
  title: string;
  author: string;
  description: string;
  cover: string;
  chapters: UranusChapter[];
}

const BASE_URL = "https://uranus-novel.com";

const HEADERS = {
  "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  Accept:
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
  "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
  Cookie: "age_ok=1; XSRF-TOKEN=token",
};

export async function fetchUranusNovel(url: string): Promise<UranusNovel> {
  // Extract novel ID from URL
  const idMatch = url.match(/\/novels\/(\d+)/);
  if (!idMatch) {
    throw new Error("Invalid Uranus novel URL");
  }
  const novelId = idMatch[1];

  const novelUrl = `${BASE_URL}/ar/novels/${novelId}`;

  const response = await fetch(novelUrl, { headers: HEADERS });
  if (!response.ok) {
    throw new Error(`Failed to fetch Uranus novel: ${response.status}`);
  }

  const html = await response.text();
  const $ = cheerio.load(html);

  // Extract title from og:title meta or title tag
  const rawTitle =
    $('meta[property="og:title"]').attr("content") ||
    $("title").text();
  const title = rawTitle
    .replace("- منصة الروايات", "")
    .replace("- أورانوس", "")
    .trim();

  // Extract description from synopsis section
  const description =
    $('meta[property="og:description"]').attr("content") ||
    $('meta[name="description"]').attr("content") ||
    $("#tab-summary p").first().text().trim();

  // Extract cover from og:image
  const cover =
    $('meta[property="og:image"]').attr("content") ||
    $(".novel-cover-large img").attr("src") ||
    "";

  // Extract author from keywords or page content  
  const keywords = $('meta[name="keywords"]').attr("content") || "";
  const keywordParts = keywords.split(",").map((k) => k.trim());
  // Format is typically: title, author, روايات, أورانوس
  let author = keywordParts[1] || "";
  if (!author || author === "روايات" || author === "أورانوس") {
    // Try to get from author section on page
    author = $(".author-name, .writer-name").first().text().trim() || "Unknown";
  }

  // Extract all chapters from the tab-chapters section
  const chapters: UranusChapter[] = [];

  // Find chapter links within the tab-chapters panel
  $("#tab-chapters a[href*='/chapters/']").each((_, el) => {
    const href = $(el).attr("href") || "";
    const chapterNumMatch = href.match(/\/chapters\/(\d+)/);
    if (chapterNumMatch) {
      const chapterNum = parseInt(chapterNumMatch[1]);
      if (!chapters.find((c) => c.chapterNum === chapterNum)) {
        // Get title from the h4 inside the link
        const chapterTitle = $(el).find("h4").text().trim() || `الفصل ${chapterNum}`;
        chapters.push({
          id: chapterNum,
          title: chapterTitle,
          url: href.startsWith("http") ? href : `${BASE_URL}${href}`,
          chapterNum,
        });
      }
    }
  });

  // If no chapters found in tab, scan the whole page
  if (chapters.length === 0) {
    $(`a[href*='/novels/${novelId}/chapters/']`).each((_, el) => {
      const href = $(el).attr("href") || "";
      const chapterNumMatch = href.match(/\/chapters\/(\d+)/);
      if (chapterNumMatch) {
        const chapterNum = parseInt(chapterNumMatch[1]);
        if (!chapters.find((c) => c.chapterNum === chapterNum)) {
          const chapterTitle =
            $(el).find("h4, strong, span").first().text().trim() ||
            `الفصل ${chapterNum}`;
          chapters.push({
            id: chapterNum,
            title: chapterTitle,
            url: href.startsWith("http") ? href : `${BASE_URL}${href}`,
            chapterNum,
          });
        }
      }
    });
  }

  // Sort chapters by number
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

export async function fetchUranusChapterContent(
  chapterUrl: string,
  novelId: string,
  chapterNum: number
): Promise<{ content: string; images: string[] }> {
  const fullUrl = chapterUrl.startsWith("http")
    ? chapterUrl
    : `${BASE_URL}/ar/novels/${novelId}/chapters/${chapterNum}`;

  const response = await fetch(fullUrl, { headers: HEADERS });
  if (!response.ok) {
    throw new Error(`Failed to fetch Uranus chapter: ${response.status}`);
  }

  const html = await response.text();
  const $ = cheerio.load(html);

  // Extract from reading-paragraph divs
  const images: string[] = [];
  const paragraphs: string[] = [];

  $(".reading-paragraph").each((_, el) => {
    // Remove comment buttons
    $(el).find("button").remove();

    // Get images
    $(el).find("img").each((__, img) => {
      const src = $(img).attr("src");
      if (src && !src.includes("avatar") && !src.includes("logo")) {
        images.push(src);
      }
    });

    const imgHtml = $(el).find("img").map((__, img) => {
      const src = $(img).attr("src");
      return src ? `<img src="${src}" style="max-width:100%;border-radius:8px;margin:10px 0" />` : "";
    }).get().join("");

    const text = $(el).clone().find("button, .paragraph-comment-btn").remove().end().text().trim();
    if (text || imgHtml) {
      paragraphs.push(`<p style="direction:rtl;text-align:right;line-height:2;margin-bottom:15px">${text}${imgHtml}</p>`);
    }
  });

  // Fallback to chapter-content-area
  if (paragraphs.length === 0) {
    const contentArea = $(".chapter-content-area");
    contentArea.find("button").remove();
    contentArea.find("img").each((_, img) => {
      const src = $(img).attr("src");
      if (src) images.push(src);
    });

    contentArea.find("p, .reading-paragraph").each((_, el) => {
      const text = $(el).text().trim();
      if (text) paragraphs.push(`<p style="direction:rtl;text-align:right;line-height:2;margin-bottom:15px">${text}</p>`);
    });
  }

  const content = `<div dir="rtl" style="text-align:right;font-family:serif;font-size:18px">${paragraphs.join("\n")}</div>`;

  return { content, images };
}
