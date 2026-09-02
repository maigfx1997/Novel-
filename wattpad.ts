export interface WattpadChapter {
  id: number;
  title: string;
  url: string;
  content?: string;
  images?: string[];
}

export interface WattpadStory {
  id: string;
  title: string;
  author: string;
  authorAvatar: string;
  description: string;
  cover: string;
  numParts: number;
  chapters: WattpadChapter[];
}

export async function fetchWattpadStory(url: string): Promise<WattpadStory> {
  // Extract story ID from URL
  const storyIdMatch = url.match(/story\/(\d+)/);
  if (!storyIdMatch) {
    throw new Error("Invalid Wattpad story URL");
  }
  const storyId = storyIdMatch[1];

  const apiUrl = `https://www.wattpad.com/api/v3/stories/${storyId}?fields=id,title,user,description,cover,numParts,parts(id,title,url,length)`;

  const response = await fetch(apiUrl, {
    headers: {
      "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch Wattpad story: ${response.status}`);
  }

  const data = await response.json();

  const story: WattpadStory = {
    id: data.id,
    title: data.title,
    author: data.user?.fullname || data.user?.name || "Unknown",
    authorAvatar: data.user?.avatar || "",
    description: data.description || "",
    cover:
      data.cover ||
      `https://img.wattpad.com/cover/${storyId}-256-k353865.jpg`,
    numParts: data.numParts || 0,
    chapters: (data.parts || []).map((part: { id: number; title: string; url: string }) => ({
      id: part.id,
      title: part.title,
      url: part.url,
    })),
  };

  return story;
}

export async function fetchWattpadChapterContent(
  chapterId: number
): Promise<{ content: string; images: string[] }> {
  // Use the Wattpad text endpoint
  const url = `https://www.wattpad.com/apiv2/storytext?id=${chapterId}&page=1&numbered=0&callback=&_=${Date.now()}`;

  const response = await fetch(url, {
    headers: {
      "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      Accept: "text/html,application/xhtml+xml",
      Referer: "https://www.wattpad.com/",
    },
  });

  if (!response.ok) {
    // Try alternative endpoint
    const altUrl = `https://www.wattpad.com/api/v3/story_parts/${chapterId}?fields=id,title,text,images`;
    const altResponse = await fetch(altUrl, {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        Accept: "application/json",
      },
    });
    if (altResponse.ok) {
      const altData = await altResponse.json();
      return {
        content: altData.text || "",
        images: altData.images || [],
      };
    }
    throw new Error(`Failed to fetch chapter: ${response.status}`);
  }

  const html = await response.text();

  // Extract images
  const imageMatches = html.match(/<img[^>]+src="([^"]+)"/g) || [];
  const images = imageMatches
    .map((img) => {
      const match = img.match(/src="([^"]+)"/);
      return match ? match[1] : null;
    })
    .filter(Boolean) as string[];

  return {
    content: html,
    images,
  };
}
