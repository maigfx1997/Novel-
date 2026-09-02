export type SourceType = "wattpad" | "novlar" | "uranus";

export interface UniversalChapter {
  id: string;
  title: string;
  url: string;
  chapterNum: number;
  content?: string;
  images?: string[];
}

export interface UniversalNovel {
  title: string;
  author: string;
  description: string;
  cover: string;
  sourceUrl: string;
  sourceType: SourceType;
  chapters: UniversalChapter[];
}

export function detectSource(url: string): SourceType | null {
  if (url.includes("wattpad.com")) return "wattpad";
  if (url.includes("novlar.com")) return "novlar";
  if (url.includes("uranus-novel.com")) return "uranus";
  return null;
}

export async function fetchNovel(url: string): Promise<UniversalNovel> {
  const source = detectSource(url);
  if (!source) {
    throw new Error("Unsupported URL. Please provide a URL from a supported source.");
  }

  if (source === "wattpad") {
    const { fetchWattpadStory } = await import("./wattpad");
    const story = await fetchWattpadStory(url);
    return {
      title: story.title,
      author: story.author,
      description: story.description,
      cover: story.cover,
      sourceUrl: url,
      sourceType: "wattpad",
      chapters: story.chapters.map((ch, i) => ({
        id: String(ch.id),
        title: ch.title,
        url: ch.url,
        chapterNum: i + 1,
      })),
    };
  }

  if (source === "novlar") {
    const { fetchNovlarNovel } = await import("./novlar");
    const novel = await fetchNovlarNovel(url);
    return {
      title: novel.title,
      author: novel.author,
      description: novel.description,
      cover: novel.cover,
      sourceUrl: url,
      sourceType: "novlar",
      chapters: novel.chapters.map((ch, i) => ({
        id: ch.id,
        title: ch.title,
        url: ch.url,
        chapterNum: ch.chapterNum || i + 1,
      })),
    };
  }

  if (source === "uranus") {
    const { fetchUranusNovel } = await import("./uranus");
    const novel = await fetchUranusNovel(url);
    return {
      title: novel.title,
      author: novel.author,
      description: novel.description,
      cover: novel.cover,
      sourceUrl: url,
      sourceType: "uranus",
      chapters: novel.chapters.map((ch, i) => ({
        id: String(ch.id),
        title: ch.title,
        url: ch.url,
        chapterNum: ch.chapterNum || i + 1,
      })),
    };
  }

  throw new Error("Unsupported source");
}

export async function fetchChapterContent(
  chapter: UniversalChapter,
  sourceType: SourceType,
  novelInfo?: { sourceUrl: string }
): Promise<{ content: string; images: string[] }> {
  if (sourceType === "wattpad") {
    const { fetchWattpadChapterContent } = await import("./wattpad");
    return fetchWattpadChapterContent(parseInt(chapter.id));
  }

  if (sourceType === "novlar") {
    const { fetchNovlarChapterContent } = await import("./novlar");
    return fetchNovlarChapterContent(chapter.url);
  }

  if (sourceType === "uranus") {
    const { fetchUranusChapterContent } = await import("./uranus");
    const novelIdMatch = novelInfo?.sourceUrl?.match(/\/novels\/(\d+)/);
    const novelId = novelIdMatch?.[1] || "";
    return fetchUranusChapterContent(chapter.url, novelId, chapter.chapterNum);
  }

  throw new Error("Unsupported source type");
}
